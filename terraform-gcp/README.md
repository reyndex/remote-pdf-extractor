# Terraform GCP

Deploys the Remote PDF Extractor on Google Cloud as a private 2nd gen Cloud Function.

What this stack sets up:

- A private Cloud Function that accepts PDF or DOCX uploads and returns extracted content
- A storage bucket that holds the function's source archive
- One service account used for Terraform credentials, Cloud Build, runtime, and invocation
- An IAM binding that lets only that service account invoke the function

Terraform Cloud state:

- Organization: `core-services`
- Workspace prefix: `remote-pdf-extractor-gcp-`

GCP resource naming:

- Cloud Function: `remote-pdf-extractor`
- Function source bucket: `<gcp_project_id>-remote-pdf-extractor-source`
- Function source object: `remote-pdf-extractor-source.zip`
- For multiple deployments in one GCP project, set `resource_name_prefix` to a unique value

Packaging: Terraform deploys the committed `../package/gcp-cloud-function.zip`; it does not use the archive provider or create archives during apply. Run `./scripts/build-function-zip.sh` from the repository root before Terraform whenever function source or requirements change.

For step-by-step setup, see [`../docs/gcp-setup.md`](../docs/gcp-setup.md).


<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.6.0 |
| <a name="requirement_google"></a> [google](#requirement\_google) | ~> 7.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_google"></a> [google](#provider\_google) | 7.29.0 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [google_cloud_run_service_iam_member.function_invoker](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_service_iam_member) | resource |
| [google_cloudfunctions2_function.remote_pdf_extractor](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions2_function) | resource |
| [google_project_service.artifact_registry_api](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) | resource |
| [google_project_service.cloud_build_api](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) | resource |
| [google_project_service.cloud_functions_api](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) | resource |
| [google_project_service.cloud_run_api](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) | resource |
| [google_project_service.cloud_storage_api](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/project_service) | resource |
| [google_storage_bucket.function_source](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) | resource |
| [google_storage_bucket_object.function_source_archive](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_object) | resource |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_available_cpu"></a> [available\_cpu](#input\_available\_cpu) | CPU allocated to each Cloud Function instance | `string` | `"1"` | no |
| <a name="input_available_memory"></a> [available\_memory](#input\_available\_memory) | Memory allocated to each Cloud Function instance | `string` | `"512Mi"` | no |
| <a name="input_billing_project_override"></a> [billing\_project\_override](#input\_billing\_project\_override) | Optional billing project for the Terraform provider itself when required by your auth setup | `string` | `""` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Optional deployment label for resource labels. When empty, derive from Terraform workspace or fall back to shared. | `string` | `""` | no |
| <a name="input_gcp_project_id"></a> [gcp\_project\_id](#input\_gcp\_project\_id) | Google Cloud project ID where the Cloud Function will be deployed | `string` | n/a | yes |
| <a name="input_gcp_region"></a> [gcp\_region](#input\_gcp\_region) | Google Cloud region for the Cloud Function | `string` | `"us-central1"` | no |
| <a name="input_ingress_settings"></a> [ingress\_settings](#input\_ingress\_settings) | Ingress mode for the Cloud Function HTTP endpoint | `string` | `"ALLOW_ALL"` | no |
| <a name="input_max_instance_count"></a> [max\_instance\_count](#input\_max\_instance\_count) | Maximum number of Cloud Function instances | `number` | `10` | no |
| <a name="input_min_instance_count"></a> [min\_instance\_count](#input\_min\_instance\_count) | Minimum number of Cloud Function instances (0 = scale to zero) | `number` | `0` | no |
| <a name="input_resource_name_prefix"></a> [resource\_name\_prefix](#input\_resource\_name\_prefix) | Optional base name for cloud resources. Defaults to remote-pdf-extractor. | `string` | `""` | no |
| <a name="input_service_account_email"></a> [service\_account\_email](#input\_service\_account\_email) | Service account email used for Terraform credentials, Cloud Build, Cloud Function runtime, and function invocation | `string` | n/a | yes |
| <a name="input_timeout_seconds"></a> [timeout\_seconds](#input\_timeout\_seconds) | Maximum execution time for the Cloud Function in seconds | `number` | `120` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_function_url"></a> [function\_url](#output\_function\_url) | The HTTPS URL of the deployed Cloud Function |
<!-- END_TF_DOCS -->
