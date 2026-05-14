locals {
  environment = trimspace(var.environment) != "" ? trimspace(var.environment) : (
    terraform.workspace != "default" ? regex("[^-]+$", terraform.workspace) : "shared"
  )

  resource_name_prefix       = trimspace(var.resource_name_prefix) != "" ? trimspace(var.resource_name_prefix) : "remote-pdf-extractor"
  name_prefix                = local.resource_name_prefix
  lambda_function_name       = local.name_prefix
  lambda_log_group_name      = "/aws/lambda/${local.lambda_function_name}"
  lambda_execution_role_name = "${local.name_prefix}-lambda-execution-role"
  lambda_security_group_name = "${local.name_prefix}-lambda-security-group"

  lambda_package_zip         = abspath("${path.module}/../package/aws-lambda.zip")
  lambda_package_exists      = fileexists(local.lambda_package_zip)
  lambda_package_source_hash = local.lambda_package_exists ? filebase64sha256(local.lambda_package_zip) : ""

  explicit_vpc_id = trimspace(var.vpc_id)
  use_vpc         = local.explicit_vpc_id != "" || var.use_default_vpc
  selected_vpc_id = local.explicit_vpc_id != "" ? local.explicit_vpc_id : (
    var.use_default_vpc ? data.aws_vpc.default[0].id : null
  )

  tags = {
    environment = local.environment
    service     = local.resource_name_prefix
    terraform   = "true"
  }
}
