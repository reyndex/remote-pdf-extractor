# AWS Setup

This guide covers the AWS Lambda deployment in `terraform-aws/`.

## What This Path Deploys

- A Lambda execution role
- A CloudWatch log group with configurable retention
- A Lambda function from a zip package
- An IAM-authenticated Lambda Function URL
- An optional security group when VPC mode is enabled

## Packaging

This deployment uses a committed zip package, not a container image. Terraform reads `package/aws-lambda.zip` and uploads that file; it does not run `pip` or create a zip during `terraform apply`.

Build the package locally before Terraform whenever `function/` or `function/requirements.txt` changes:

```bash
./scripts/build-function-zip.sh
```

The AWS zip keeps source files at the archive root and installs dependencies under `_deps/`. Terraform sets `PYTHONPATH=/var/task/_deps` so Lambda can import those dependencies while the Lambda console still shows the handler files separately from vendored packages.

No Docker or ECR setup is required.

## Prerequisites

- An AWS account
- Terraform CLI
- Terraform Cloud access to the configured backend organization
- One AWS IAM user or role for deployment and invocation
- `python3` and `bash` available where you run `./scripts/build-function-zip.sh`

## IAM Identity

Use one AWS IAM user or role for:

- Terraform credentials
- Lambda deployment
- Signed Function URL invocation

For a low-friction setup, attach this AWS managed policy to that identity:

- AdministratorAccess

Terraform creates the Lambda execution role separately. The execution role is used by Lambda at runtime and includes `AWSLambdaBasicExecutionRole` for CloudWatch logging.

## Terraform Cloud

This Terraform root uses Terraform Cloud remote state by default:

- organization: `core-services`
- workspace prefix: `remote-pdf-extractor-aws-`

Run Terraform from:

```text
terraform-aws/
```

Common optional variables:

| Variable | Example |
|---|---|
| `aws_region` | `us-east-1`; defaults to `us-west-2` |

Required AWS credentials:

| Variable | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | access key id for the IAM identity |
| `AWS_SECRET_ACCESS_KEY` | secret access key for the IAM identity |
| `AWS_SESSION_TOKEN` | optional, only for temporary credentials |

Other optional variables:

| Variable | Default |
|---|---|
| `resource_name_prefix` | `remote-pdf-extractor` |
| `environment` | `shared`; optional tag label |
| `python_runtime` | `python3.13` |
| `lambda_handler` | `main.handler` |
| `lambda_architecture` | `arm64` |
| `lambda_memory_mb` | `1024` |
| `timeout_seconds` | `120` |
| `log_retention_in_days` | `14` |
| `vpc_id` | `""` |
| `use_default_vpc` | `false` |

Supported runtimes for this zip packaging path are `python3.12` and `python3.13`. If you change `python_runtime` or `lambda_architecture`, rebuild the package with matching values before committing it:

```bash
AWS_PYTHON_RUNTIME=python3.13 LAMBDA_ARCHITECTURE=arm64 ./scripts/build-function-zip.sh
```

## VPC

No VPC is used by default.

To attach the Lambda to a specific VPC:

```hcl
vpc_id = "vpc-0123456789abcdef0"
```

To attach the Lambda to the account default VPC:

```hcl
use_default_vpc = true
```

When VPC mode is enabled, Terraform selects the VPC's subnets and creates one outbound-only security group for the Lambda.

VPC mode affects the Lambda's outbound/private networking only. The Function URL remains public and IAM-authenticated. If a VPC-attached Lambda needs internet access, the selected VPC subnets need a NAT path or appropriate VPC endpoints.

## Deploy

```bash
./scripts/build-function-zip.sh
git add package/aws-lambda.zip package/gcp-cloud-function.zip

cd terraform-aws
terraform init
terraform workspace select -or-create development
terraform apply
```

After apply, save:

```text
function_url = "https://..."
```

## Invoke

The Function URL uses:

```text
authorization_type = AWS_IAM
```

Requests must be signed with AWS Signature Version 4. The invoking identity needs both:

- `lambda:InvokeFunctionUrl`
- `lambda:InvokeFunction`

The invoking IAM identity can be the same identity used for deployment or a separate identity with invoke permissions.

Set:

```bash
export AWS_REGION=us-east-1
export FUNCTION_URL="$(terraform -chdir=terraform-aws output -raw function_url)"
```

Example with `curl` and SigV4:

```bash
curl --request POST \
  --url "${FUNCTION_URL}" \
  --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" \
  --aws-sigv4 "aws:amz:${AWS_REGION}:lambda" \
  --header "x-amz-security-token: ${AWS_SESSION_TOKEN}" \
  --form "file=@document.pdf"
```

If you are not using temporary credentials, omit the `x-amz-security-token` header.

DOCX uploads use the same call shape:

```bash
curl ... --form "file=@resume.docx"
```

Lambda Function URLs use Lambda synchronous invocation limits, so direct multipart uploads are limited by AWS before the app sees the request. For larger files, use `file_url`; the Lambda downloads the file server-side and applies the app's 20 MB file limit.

You can also send a generic HTTP(S) download URL instead of uploading bytes:

```bash
curl --request POST \
  --url "${FUNCTION_URL}" \
  --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" \
  --aws-sigv4 "aws:amz:${AWS_REGION}:lambda" \
  --header "content-type: application/json" \
  --header "x-amz-security-token: ${AWS_SESSION_TOKEN}" \
  --data '{"file_url":"https://example.com/document.pdf"}'
```

If a multipart `file` and `file_url` are both present, the uploaded file takes priority.

## Notes

- The Lambda handler entry is `main.handler` by default. `function/main.py` re-exports `handler` from `function/aws_handler.py`.
- The Function URL is reachable on the public internet but protected by IAM.
- `urlextract` downloads the IANA TLD list to `/tmp/urlextract` on the first invocation per execution environment; warm invocations reuse the cached file.
