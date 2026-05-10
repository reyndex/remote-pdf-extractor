locals {
  workspace_name = trimspace(var.TFC_WORKSPACE_NAME) != "" ? trimspace(var.TFC_WORKSPACE_NAME) : terraform.workspace

  environment = trimspace(var.environment) != "" ? trimspace(var.environment) : (
    local.workspace_name != "default" ? regex("[^-]+$", local.workspace_name) : "shared"
  )

  resource_name_prefix            = trimspace(var.resource_name_prefix) != "" ? trimspace(var.resource_name_prefix) : "remote-pdf-extractor"
  name_prefix                     = local.resource_name_prefix
  lambda_function_name            = local.name_prefix
  lambda_log_group_name           = "/aws/lambda/${local.lambda_function_name}"
  lambda_execution_role_name      = "${local.name_prefix}-lambda-execution-role"
  lambda_security_group_name      = "${local.name_prefix}-lambda-security-group"
  function_url_ssm_parameter_name = trimspace(var.function_url_ssm_parameter_name)

  lambda_package_zip         = abspath("${path.module}/../package/aws-lambda.zip")
  lambda_package_exists      = fileexists(local.lambda_package_zip)
  lambda_package_source_hash = local.lambda_package_exists ? filebase64sha256(local.lambda_package_zip) : ""

  explicit_vpc_id = trimspace(var.vpc_id)
  use_vpc         = local.explicit_vpc_id != "" || var.use_default_vpc
  selected_vpc_id = local.explicit_vpc_id != "" ? local.explicit_vpc_id : (
    var.use_default_vpc ? data.aws_vpc.default[0].id : null
  )

  tags = {
    Environment = local.environment
    Service     = local.resource_name_prefix
    Terraform   = true
  }
}
