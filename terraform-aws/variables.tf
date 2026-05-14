variable "resource_name_prefix" {
  description = "Optional base name for account-scoped AWS resources. Defaults to remote-pdf-extractor."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Optional deployment label for tags. When empty, derive from Terraform workspace or fall back to shared."
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region for the Lambda function"
  type        = string
  default     = "us-west-2"
}

variable "python_runtime" {
  description = "Lambda Python runtime identifier. This zip-packaging path supports the AL2023 runtimes used by python3.12 and python3.13."
  type        = string
  default     = "python3.13"

  validation {
    condition     = contains(["python3.12", "python3.13"], var.python_runtime)
    error_message = "python_runtime must be python3.12 or python3.13."
  }
}

variable "lambda_handler" {
  description = "Lambda handler entry point. Defaults to main.handler so AWS enters through the same shared router as GCP."
  type        = string
  default     = "main.handler"
}

variable "lambda_architecture" {
  description = "Lambda CPU architecture"
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["arm64", "x86_64"], var.lambda_architecture)
    error_message = "lambda_architecture must be either arm64 or x86_64."
  }
}

variable "lambda_memory_mb" {
  description = "Memory allocated to the Lambda function in MB"
  type        = number
  default     = 1024
}

variable "timeout_seconds" {
  description = "Maximum execution time for the Lambda function in seconds"
  type        = number
  default     = 120
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention for the Lambda log group"
  type        = number
  default     = 14
}

variable "environment_variables" {
  description = "Additional environment variables passed to the Lambda function"
  type        = map(string)
  default     = {}
}

variable "vpc_id" {
  description = "Optional VPC ID for Lambda attachment. When empty, no VPC is used unless use_default_vpc is true."
  type        = string
  default     = ""
}

variable "use_default_vpc" {
  description = "Attach the Lambda to the account default VPC when vpc_id is empty"
  type        = bool
  default     = false
}
