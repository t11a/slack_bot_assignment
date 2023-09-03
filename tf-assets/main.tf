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

# Variables
variable "system_name" {
  default = "slack_assignment"
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

# Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name               = "${var.system_name}_lambda_layer"
  compatible_runtimes      = ["python3.9", "python3.11"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.layer_zip.output_path
  source_code_hash         = data.archive_file.layer_zip.output_base64sha256
}

# Function
resource "aws_lambda_function" "slack_bot" {
  function_name = "${var.system_name}_slack_bot"

  handler          = "handler.lambda_handler"
  filename         = data.archive_file.function_zip.output_path
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_iam_role.arn
  source_code_hash = data.archive_file.function_zip.output_base64sha256
  layers           = ["${aws_lambda_layer_version.lambda_layer.arn}"]
}

resource "aws_lambda_function_event_invoke_config" "slack_bot" {
  function_name                = aws_lambda_function.slack_bot.function_name
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
