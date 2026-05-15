data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_execution" {
  name        = local.lambda_execution_role_name
  description = "Execution role for the Remote PDF Extractor Lambda"

  tags = {
    name = local.lambda_execution_role_name
  }

  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  lifecycle {
    precondition {
      condition     = length(local.lambda_execution_role_name) <= 64
      error_message = "The Lambda execution role name must be 64 characters or fewer. Shorten resource_name_prefix."
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  count = local.use_vpc ? 1 : 0

  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
