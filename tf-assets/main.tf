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

# Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name               = "${var.system_name}_lambda_layer"
  compatible_runtimes      = ["python3.9", "python3.11"]
  compatible_architectures = ["x86_64"]
  filename                 = data.archive_file.layer_zip.output_path
  source_code_hash         = data.archive_file.layer_zip.output_base64sha256
}
