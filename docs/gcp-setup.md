# GCP setup

Deploys an authenticated Cloud Functions 2nd gen extractor and source bucket. [Terraform reference](../terraform-gcp/README.md) owns variables/resources; [public API](../README.md) owns request/response behavior.

## Prerequisites

Use a billing-enabled project with Cloud Resource Manager, IAM, and Service Usage APIs enabled. Terraform enables runtime Cloud Functions/Build/Run, Artifact Registry, and Storage APIs.

The current stack uses one service account for Terraform, build, runtime, and invocation, with Editor and Cloud Run Admin project roles; Terraform grants `roles/run.invoker` on the function. Supply its JSON key through local `GOOGLE_APPLICATION_CREDENTIALS` or runner secret storage; never commit it. Set Terraform `gcp_project_id` and `service_account_email`.

Terraform Cloud defaults: organization `core-services`, workspace prefix `remote-pdf-extractor-gcp-`. Region defaults to `us-west1`.

## Deploy

```bash
./scripts/build-function-zip.sh
cd terraform-gcp
terraform init
terraform workspace select -or-create development
terraform plan
terraform apply
```

Commit package artifacts with runtime changes. Terraform uploads `package/gcp-cloud-function.zip`, not a newly built archive. Python runtime is `python313`; source/requirements are at archive root and wheels under `_vendor/`. Cloud Build uses `GOOGLE_VENDOR_PIP_DEPENDENCIES=_vendor`. Keep `functions-framework` pinned in `function/requirements.txt`: Google Cloud can add it automatically when omitted, but pinning keeps builds consistent.

`ingress_settings` defaults to `ALLOW_ALL`, which permits authenticated public callers; the stricter `ALLOW_INTERNAL_AND_GCLB` and `ALLOW_INTERNAL_ONLY` values require the caller path to traverse the allowed network boundary. IAM/ID-token authentication remains required.

## Invoke

Use Terraform's `function_url` output as both URL and ID-token audience. With application credentials configured:

```python
import os
import google.auth.transport.requests
import google.oauth2.id_token
import httpx

url = os.environ["FUNCTION_URL"]
token = google.oauth2.id_token.fetch_id_token(
    google.auth.transport.requests.Request(), url
)
with open("document.pdf", "rb") as document:
    response = httpx.post(
        url, files={"file": document},
        headers={"Authorization": f"Bearer {token}"}, timeout=120,
    )
result = response.json()
```

DOCX uses the same upload shape. For remote input use `json={"file_url": "..."}` instead of `files`. Handle HTTP/API errors per README; avoid logging extracted content. Entry point `extract_document` in `main.py` re-exports the GCP adapter.
