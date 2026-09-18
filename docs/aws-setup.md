# AWS setup

Deploys the shared extractor as a Lambda with IAM-authenticated Function URL, logging role, and optional VPC security group. [Terraform reference](../terraform-aws/README.md) owns variables/resources; [public API](../README.md) owns request/response behavior.

## Deploy

Requires an AWS identity with permissions to manage the Terraform-declared Lambda, IAM, log group, Function URL, and (in VPC mode) security group resources; export `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and, for temporary credentials, `AWS_SESSION_TOKEN` for Terraform runs. Also requires Terraform Cloud access (`core-services`, prefix `remote-pdf-extractor-aws-`), Python, and Bash. Keep credentials in local/runner secret storage.

```bash
./scripts/build-function-zip.sh
cd terraform-aws
terraform init
terraform workspace select -or-create development
terraform plan
terraform apply
```

Commit consumed package artifacts with runtime changes. Terraform reads `package/aws-lambda.zip`; it does not build dependencies. Source is at archive root, dependencies under `_deps/`, with `PYTHONPATH=/var/task/_deps`. No Docker/ECR is needed.

Defaults are Python 3.13 ARM64 in `us-west-2`. Supported package runtimes are Python 3.12/3.13; rebuild to match runtime/architecture changes:

```bash
AWS_PYTHON_RUNTIME=python3.13 LAMBDA_ARCHITECTURE=arm64 ./scripts/build-function-zip.sh
```

No VPC by default. `vpc_id` or `use_default_vpc=true` selects subnets and an outbound-only security group. VPC mode changes outbound networking, not public Function URL reachability/auth; internet access needs NAT or suitable endpoints.

## Invoke

The URL is publicly reachable but requires SigV4 and both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction`. Invocation may use a separate identity from deployment.

From the repository root, with securely supplied AWS credentials:

```bash
export AWS_REGION=us-west-2
export FUNCTION_URL="$(terraform -chdir=terraform-aws output -raw function_url)"
curl --request POST --url "${FUNCTION_URL}" \
  --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" \
  --aws-sigv4 "aws:amz:${AWS_REGION}:lambda" \
  --header "x-amz-security-token: ${AWS_SESSION_TOKEN}" \
  --form "file=@document.pdf"
```

Omit the token header for non-temporary credentials. Use the same auth with JSON `file_url` for larger files: Lambda synchronous payload limits apply before the 20 MB application limit. Never log signed URLs or source data.

`main.handler` re-exports the AWS adapter. `urlextract` needs first-invocation network access to download its IANA TLD list into `/tmp/urlextract`; warm invocations reuse it.
