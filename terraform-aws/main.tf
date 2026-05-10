resource "aws_security_group" "lambda" {
  count = local.use_vpc ? 1 : 0

  name        = local.lambda_security_group_name
  description = "Outbound access for the Remote PDF Extractor Lambda"
  vpc_id      = local.selected_vpc_id

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = local.lambda_security_group_name
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = local.lambda_log_group_name
  retention_in_days = var.log_retention_in_days

  tags = {
    Name = local.lambda_log_group_name
  }
}

resource "aws_lambda_function" "remote_pdf_extractor" {
  function_name    = local.lambda_function_name
  description      = "Extracts text from uploaded PDF and DOCX documents"
  filename         = local.lambda_package_zip
  source_code_hash = local.lambda_package_source_hash
  runtime          = var.python_runtime
  handler          = var.lambda_handler
  role             = aws_iam_role.lambda_execution.arn
  memory_size      = var.lambda_memory_mb
  timeout          = var.timeout_seconds
  architectures    = [var.lambda_architecture]

  environment {
    variables = merge(
      {
        REMOTE_PDF_EXTRACTOR_PROVIDER = "aws"
        PYTHONPATH                    = "/var/task/_deps"
      },
      var.environment_variables,
    )
  }

  dynamic "vpc_config" {
    for_each = local.use_vpc ? [1] : []
    content {
      subnet_ids         = data.aws_subnets.lambda[0].ids
      security_group_ids = [aws_security_group.lambda[0].id]
    }
  }

  tags = {
    Name = local.lambda_function_name
  }

  lifecycle {
    precondition {
      condition     = local.lambda_package_exists
      error_message = "Missing ../package/aws-lambda.zip. Run ./scripts/build-function-zip.sh from the repository root before terraform apply."
    }

    precondition {
      condition     = length(local.lambda_function_name) <= 64 && can(regex("^[A-Za-z0-9-_]+$", local.lambda_function_name))
      error_message = "The Lambda function name must be 64 characters or fewer and contain only letters, numbers, hyphens, or underscores. Adjust resource_name_prefix."
    }

    precondition {
      condition     = local.use_vpc ? length(data.aws_subnets.lambda[0].ids) > 0 : true
      error_message = "The selected VPC must contain at least one subnet."
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_vpc_access,
  ]
}

resource "aws_lambda_function_url" "remote_pdf_extractor" {
  function_name      = aws_lambda_function.remote_pdf_extractor.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_ssm_parameter" "function_url" {
  count = local.function_url_ssm_parameter_name != "" ? 1 : 0

  name        = local.function_url_ssm_parameter_name
  description = "Lambda Function URL for the deployed Remote PDF Extractor"
  type        = "String"
  value       = aws_lambda_function_url.remote_pdf_extractor.function_url
}
