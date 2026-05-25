locals {
  environment = trimspace(var.environment) != "" ? trimspace(var.environment) : (
    terraform.workspace != "default" ? regex("[^-]+$", terraform.workspace) : "shared"
  )

  resource_name_prefix = trimspace(var.resource_name_prefix) != "" ? trimspace(var.resource_name_prefix) : "remote-pdf-extractor"
  name_prefix          = local.resource_name_prefix

  cloud_function_name       = local.name_prefix
  function_source_bucket    = "${var.gcp_project_id}-${local.name_prefix}-source"
  function_source_object    = "${local.cloud_function_name}-source.zip"
  function_source_zip       = abspath("${path.module}/../package/gcp-cloud-function.zip")
  function_source_exists    = fileexists(local.function_source_zip)
  function_source_hash      = local.function_source_exists ? filemd5(local.function_source_zip) : ""
  function_vendor_directory = "_vendor"

  service_account_email         = trimspace(var.service_account_email)
  service_account_member        = "serviceAccount:${local.service_account_email}"
  service_account_resource_name = "projects/${var.gcp_project_id}/serviceAccounts/${local.service_account_email}"

  resource_labels = {
    app         = local.resource_name_prefix
    environment = local.environment
    managed_by  = "terraform"
    service     = local.resource_name_prefix
  }
}
