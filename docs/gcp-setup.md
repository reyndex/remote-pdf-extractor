# GCP Setup

This guide covers the Google Cloud setup for the authenticated Cloud Functions deployment in `terraform-gcp/`.

## What this path deploys

- An authenticated Cloud Functions 2nd gen HTTP function with configurable ingress
- A source bucket for the function archive
- One service account used for Terraform credentials, Cloud Build, runtime, and invocation
- A Cloud Run invoker IAM binding for that service account

## Prerequisites

- A GCP project with billing enabled
- A service account for deployment and invocation
- Terraform CLI
- Terraform Cloud access to the configured backend organization

Enable these APIs in the Cloud Console before the first Terraform run:

- Cloud Resource Manager API
- Identity and Access Management (IAM) API
- Service Usage API

Terraform will enable the runtime APIs the stack needs, including:

- Cloud Functions API
- Cloud Build API
- Cloud Run Admin API
- Artifact Registry API
- Cloud Storage API

## Service account

Create one service account and use it for:

- Terraform credentials
- Cloud Build source builds
- Cloud Function runtime identity
- Authenticated calls to the function

Grant these project roles to the service account:

- Editor
- Cloud Run Admin

Create a JSON key for this service account. For local Terraform, set `GOOGLE_APPLICATION_CREDENTIALS` to the key path. For Terraform Cloud or another remote runner, store the JSON key in that runner's secret storage and set the same service account email in `service_account_email`.

Terraform grants this service account `roles/run.invoker` on the function so authenticated calls from this account are accepted.

## Runtime and dependencies

This stack deploys the function on Python 3.13. In Terraform, Google Cloud expects the runtime ID `python313`.

Terraform reads `package/gcp-cloud-function.zip` and uploads that file to the function source bucket; it does not create the zip during apply.

Build the package locally before Terraform whenever `function/` or `function/requirements.txt` changes:

```bash
./scripts/build-function-zip.sh
```

The GCP zip keeps source files and `requirements.txt` at the archive root and stores copied pip wheels under `_vendor/`. Terraform sets `GOOGLE_VENDOR_PIP_DEPENDENCIES=_vendor` in the Cloud Functions build config so Cloud Build uses the packaged wheels instead of downloading dependencies at deploy time.

`function/requirements.txt` keeps `functions-framework` pinned explicitly. Google Cloud can add it automatically during builds if you omit it, but Google recommends pinning it in `requirements.txt` to keep builds consistent.

## Terraform Cloud

This Terraform root uses Terraform Cloud remote state by default:

- organization: `core-services`
- workspace prefix: `remote-pdf-extractor-gcp-`

Run Terraform from:

```text
terraform-gcp/
```

Required Terraform variables:

| Variable | Example |
|---|---|
| `gcp_project_id` | `my-project-id` |
| `service_account_email` | `remote-pdf-extractor@my-project-id.iam.gserviceaccount.com` |

Common optional variables:

| Variable | Default |
|---|---|
| `gcp_region` | `us-central1` |
| `ingress_settings` | `ALLOW_ALL` |
| `resource_name_prefix` | `remote-pdf-extractor` |
| `environment` | `shared`; optional resource label |
| `max_instance_count` | `10` |
| `min_instance_count` | `0` |
| `available_memory` | `512Mi` |
| `available_cpu` | `1` |
| `timeout_seconds` | `120` |

Required local environment variable:

| Variable | Value |
|---|---|
| `GOOGLE_APPLICATION_CREDENTIALS` | path to the `service_account_email` JSON key |

## Apply

```bash
./scripts/build-function-zip.sh
git add package/aws-lambda.zip package/gcp-cloud-function.zip

cd terraform-gcp
terraform init
terraform workspace select -or-create development
terraform apply
```

Ingress:

- `ingress_settings = "ALLOW_ALL"` keeps the function URL reachable for callers authenticated with Google IAM / ID tokens
- `ALLOW_INTERNAL_AND_GCLB` or `ALLOW_INTERNAL_ONLY` are stricter options; use them only when your caller path goes through the allowed network boundary

After apply, save:

```text
function_url = "https://..."
```

Use that value as both:

- The request URL
- The ID-token audience

## Invoke

Set:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/remote-pdf-extractor.json
export FUNCTION_URL="https://YOUR_FUNCTION_URL"
```

Python example (PDF or DOCX upload):

```python
import os

import google.auth.transport.requests
import google.oauth2.id_token
import httpx


function_url = os.environ["FUNCTION_URL"]
token = google.oauth2.id_token.fetch_id_token(
    google.auth.transport.requests.Request(),
    function_url,
)

with open("document.pdf", "rb") as f:
    response = httpx.post(
        function_url,
        files={"file": ("document.pdf", f.read(), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
if response.status_code not in (200, 400, 500):
    response.raise_for_status()
result = response.json()
if not result["ok"]:
    raise SystemExit(result["error"]["message"])

data = result["data"]
print("markdown chars:", len(data["markdown"]))
print("email addresses:", data["email_addresses"])
print("link URLs:", data["link_urls"])
print("phone numbers:", data["phone_numbers"])
```

DOCX uploads use the same shape, just swap the filename and content type (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`). The server detects format from file magic bytes regardless of the declared content type.

You can also send a generic HTTP(S) download URL instead of uploading bytes:

```python
response = httpx.post(
    function_url,
    json={"file_url": "https://example.com/document.pdf"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=120,
)
```

If a multipart `file` and `file_url` are both present, the uploaded file takes priority.

## Notes

- The GCP entry point is `extract_document` in `function/main.py`, which re-exports the handler from `function/gcp_handler.py`
