# Terraform AWS

Deploys the Remote PDF Extractor on AWS as a Lambda behind an IAM-authenticated Function URL.

What this stack sets up:

- A Lambda function that accepts PDF or DOCX uploads and returns extracted content
- An IAM role and a CloudWatch log group for the Lambda
- An IAM-authenticated Function URL
- An optional security group when VPC mode is enabled

Terraform Cloud state:

- Organization: `core-services`
- Workspace prefix: `remote-pdf-extractor-aws-`

AWS resource naming:

- Lambda function: `remote-pdf-extractor`
- IAM execution role: `remote-pdf-extractor-lambda-execution-role`
- VPC security group: `remote-pdf-extractor-lambda-security-group`
- For multiple deployments in one AWS account, set `resource_name_prefix` to a unique value

Packaging: zip-based (no Docker, no ECR). Terraform deploys the committed `../package/aws-lambda.zip`; it does not install dependencies or create archives during apply. Run `./scripts/build-function-zip.sh` from the repository root before Terraform whenever function source or requirements change.

AWS Lambda Function URLs use Lambda synchronous invocation limits. Direct multipart uploads are limited by AWS before app code runs; use `file_url` for larger files so the Lambda downloads the file server-side and applies the app's 20 MB file limit.

For step-by-step setup, see [`../docs/aws-setup.md`](../docs/aws-setup.md).

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.15.3 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.41.0 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [aws_cloudwatch_log_group.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_role.lambda_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.lambda_basic_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.lambda_vpc_access](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_function.remote_pdf_extractor](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_lambda_function_url.remote_pdf_extractor](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function_url) | resource |
| [aws_security_group.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_iam_policy_document.lambda_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_partition.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/partition) | data source |
| [aws_subnets.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/subnets) | data source |
| [aws_vpc.default](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/vpc) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region for the Lambda function | `string` | `"us-west-2"` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Optional deployment label for tags. When empty, derive from Terraform workspace or fall back to shared. | `string` | `""` | no |
| <a name="input_environment_variables"></a> [environment\_variables](#input\_environment\_variables) | Additional environment variables passed to the Lambda function | `map(string)` | `{}` | no |
| <a name="input_lambda_architecture"></a> [lambda\_architecture](#input\_lambda\_architecture) | Lambda CPU architecture | `string` | `"arm64"` | no |
| <a name="input_lambda_handler"></a> [lambda\_handler](#input\_lambda\_handler) | Lambda handler entry point. Defaults to main.handler so AWS enters through the same shared router as GCP. | `string` | `"main.handler"` | no |
| <a name="input_lambda_memory_mb"></a> [lambda\_memory\_mb](#input\_lambda\_memory\_mb) | Memory allocated to the Lambda function in MB | `number` | `1024` | no |
| <a name="input_log_retention_in_days"></a> [log\_retention\_in\_days](#input\_log\_retention\_in\_days) | CloudWatch log retention for the Lambda log group | `number` | `14` | no |
| <a name="input_python_runtime"></a> [python\_runtime](#input\_python\_runtime) | Lambda Python runtime identifier. This zip-packaging path supports the AL2023 runtimes used by python3.12 and python3.13. | `string` | `"python3.13"` | no |
| <a name="input_resource_name_prefix"></a> [resource\_name\_prefix](#input\_resource\_name\_prefix) | Optional base name for account-scoped AWS resources. Defaults to remote-pdf-extractor. | `string` | `""` | no |
| <a name="input_timeout_seconds"></a> [timeout\_seconds](#input\_timeout\_seconds) | Maximum execution time for the Lambda function in seconds | `number` | `120` | no |
| <a name="input_use_default_vpc"></a> [use\_default\_vpc](#input\_use\_default\_vpc) | Attach the Lambda to the account default VPC when vpc\_id is empty | `bool` | `false` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | Optional VPC ID for Lambda attachment. When empty, no VPC is used unless use\_default\_vpc is true. | `string` | `""` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_function_arn"></a> [function\_arn](#output\_function\_arn) | Lambda function ARN |
| <a name="output_function_name"></a> [function\_name](#output\_function\_name) | Lambda function name |
| <a name="output_function_url"></a> [function\_url](#output\_function\_url) | Lambda Function URL |
<!-- END_TF_DOCS -->
