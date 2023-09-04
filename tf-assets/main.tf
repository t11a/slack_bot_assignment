# Terraform Settings
terraform {
  required_version = "1.5.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.15.0"
    }
  }
}

# Provider
provider "aws" {
  region = "ap-northeast-1"
}

# Data
data "aws_caller_identity" "current" {}

# Variables
variable "system_name" {
  default = "slack_assignment"
}

variable "slack_token" {}
variable "slack_signing_secret" {}

locals {
  dynamodb_table_names = {
    messages    = "Messages"
    user_counts = "UserCounts"
  }
}

# Archive
data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = "../build/layer"
  output_path = "../lambda/layer.zip"
}

data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "../build/function"
  output_path = "../lambda/function.zip"
}

data "archive_file" "function_firehose_zip" {
  type        = "zip"
  source_dir  = "../build/function_firehose"
  output_path = "../lambda/function_firehose.zip"
}

# Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name               = "${var.system_name}_lambda_layer"
  compatible_runtimes      = ["python3.9", "python3.11"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.layer_zip.output_path
  source_code_hash         = data.archive_file.layer_zip.output_base64sha256
}

# Function for Slack
resource "aws_lambda_function" "slack_bot" {
  function_name = "${var.system_name}_slack_bot"

  handler          = "handler.lambda_handler"
  filename         = data.archive_file.function_zip.output_path
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_iam_role.arn
  source_code_hash = data.archive_file.function_zip.output_base64sha256
  timeout          = 10
  layers           = ["${aws_lambda_layer_version.lambda_layer.arn}"]
  environment {
    variables = {
      SLACK_TOKEN          = var.slack_token
      SLACK_SIGNING_SECRET = var.slack_signing_secret
    }
  }
}

resource "aws_lambda_function_event_invoke_config" "slack_bot" {
  function_name                = aws_lambda_function.slack_bot.function_name
  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 0
}

# Function for Firehose
resource "aws_lambda_function" "firehose_transform" {
  function_name = "${var.system_name}_firehose_transform"

  handler          = "handler.lambda_handler"
  filename         = data.archive_file.function_firehose_zip.output_path
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_iam_role.arn
  source_code_hash = data.archive_file.function_firehose_zip.output_base64sha256
  timeout          = 30
}

resource "aws_lambda_function_event_invoke_config" "firehose" {
  function_name                = aws_lambda_function.firehose_transform.function_name
  maximum_event_age_in_seconds = 60
  maximum_retry_attempts       = 0
}


# Role
resource "aws_iam_role" "lambda_iam_role" {
  name = "${var.system_name}_iam_role"

  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
POLICY
}

# Policy
resource "aws_iam_role_policy" "lambda_access_policy" {
  name   = "${var.system_name}_lambda_access_policy"
  role   = aws_iam_role.lambda_iam_role.id
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
POLICY
}

# Attach DDB Policy
resource "aws_iam_role_policy_attachment" "dynamodb_full_access" {
  role       = aws_iam_role.lambda_iam_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# DynamoDB Tables - Messages, UserCounts
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table
resource "aws_dynamodb_table" "messages" {
  name         = local.dynamodb_table_names.messages
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"
  range_key    = "time_to_username"

  attribute {
    name = "username"
    type = "S"
  }

  attribute {
    name = "time_to_username"
    type = "S"
  }
}

resource "aws_dynamodb_table" "user_counts" {
  name         = local.dynamodb_table_names.user_counts
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }
}

# Kinesis Data Stream
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kinesis_stream.html
resource "aws_kinesis_stream" "stream" {
  name = "${var.system_name}_data_stream"
  #shard_count      = 1
  retention_period = 24

  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }
}

# https://registry.terraform.io/providers/BigEyeLabs/aws-test/latest/docs/resources/dynamodb_kinesis_streaming_destination
resource "aws_dynamodb_kinesis_streaming_destination" "example" {
  stream_arn = aws_kinesis_stream.stream.arn
  table_name = aws_dynamodb_table.messages.name
}

# S3 Bucket
resource "aws_s3_bucket" "firehose_destination" {
  bucket = "firehose-destination-ap-northeast-1-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "athena_query_result" {
  bucket = "athena-query-result-ap-northeast-1-${data.aws_caller_identity.current.account_id}"
}


# Kinesis Data Firehose
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kinesis_firehose_delivery_stream
resource "aws_kinesis_firehose_delivery_stream" "extended_s3_stream" {
  name        = "${var.system_name}_kinesis_firehose"
  destination = "extended_s3"
  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.stream.arn
    role_arn           = aws_iam_role.firehose_role.arn
  }
  extended_s3_configuration {
    role_arn           = aws_iam_role.firehose_role.arn
    bucket_arn         = aws_s3_bucket.firehose_destination.arn
    buffering_interval = 60

    prefix              = "${var.system_name}/success/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "${var.system_name}/error/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}"


    processing_configuration {
      enabled = "true"
      processors {
        type = "Lambda"
        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.firehose_transform.arn}:$LATEST"
        }
      }
    }
  }
}

# IAM Role for Firehose
resource "aws_iam_role" "firehose_role" {
  name = "${var.system_name}_firehose_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "firehose_s3_lambda" {
  statement {
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject"
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.firehose_destination.id}",
      "arn:aws:s3:::${aws_s3_bucket.firehose_destination.id}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "kinesis:*"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "lambda:*"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "firehose_policy" {
  name   = "${var.system_name}_firehose_policy"
  policy = data.aws_iam_policy_document.firehose_s3_lambda.json
}

resource "aws_iam_role_policy_attachment" "firehose_att" {
  role       = aws_iam_role.firehose_role.name
  policy_arn = aws_iam_policy.firehose_policy.arn
}
