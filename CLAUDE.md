# Remote PDF Extractor - AI Agent Guide

Remote PDF Extractor is a standalone open-source service that extracts clean markdown and structured contact/link data from PDF and DOCX documents.

Use this guide when changing repository behavior, packaging, deployment templates, or documentation. Keep changes scoped to the extractor's public API and the integration points documented in this repo.

## Start Here

Read these local files before changing behavior, architecture, deployment, or extraction logic:

- `README.md`
- `docs/README.md`
- `docs/gcp-setup.md`
- `docs/aws-setup.md`
- `function/extractor/core.py`
- `function/main.py`
- `function/gcp_handler.py`
- `function/aws_handler.py`
- `function/extractor/request_payload.py`
- `function/extractor/remote_file.py`
- `function/requirements.txt`
- `scripts/build-function-zip.sh`
- `terraform-gcp/README.md`
- `terraform-aws/README.md`

## Development Rules

- Keep the request/response contract in `README.md` aligned with code. Do not document formats, fields, deployment targets, limits, or auth behavior that do not exist.
- Remote PDF Extractor owns document extraction only. Do not add caller-specific business workflow, persistence, orchestration, or authorization decisions here.
- Treat all callers and downstream systems as external integrations. Keep the public request/response contract generic and reusable.
- Every app-level response uses the standard `{ ok, data, error }` envelope and includes an `X-Request-Id` response header. Successful responses use HTTP `200`; application errors use this service's documented error status set.
- Multipart `file` input takes priority over `file_url` when both are present.
- Detect formats by file signature, not content type or file extension.
- Keep the 20 MB app-level file-size limit unless API documentation and deployment constraints are changed together.
- Preserve documented phone-number behavior: keep leading `+` only when the source contained it; otherwise return digits only.
- Closed extractor states, document formats, and request fields should use module-owned enums or typed constants. Keep standard HTTP methods, MIME types, headers, URL schemes, Terraform values, and provider/runtime labels inline or local unless repeated validation logic needs a named helper, and preserve exact external wire values.
- Never log secrets, signed URLs, raw documents, extracted document text, raw email addresses/phone numbers beyond necessary local debugging, or sensitive source material.
- Build deployment packages when `function/` or `function/requirements.txt` changes, and commit generated `package/` artifacts when the deployment flow consumes them.
- Keep the default deployment regions and setup examples aligned on AWS `us-west-2` and GCP `us-west1` unless intentionally documenting a regional exception.

## Repo Shape

- `function/extractor/`: shared extraction logic, request parsing, remote download handling, response schema, enums, constants, and error messages
- `function/main.py`: entry router
- `function/gcp_handler.py`: Google Cloud Functions request adapter
- `function/aws_handler.py`: AWS Lambda event adapter
- `scripts/build-function-zip.sh`: package builder for both deployment targets
- `package/`: committed deployment zips consumed by Terraform
- `terraform-gcp/`: Google Cloud Functions deployment
- `terraform-aws/`: AWS Lambda deployment
- `docs/`: setup and deployment guides

## Integration Boundaries

- Any client may call this service. Changes to file URL/upload handling, auth, retries, expected response envelopes, accepted formats, file-size policy, or contact/link handling can require client updates.
- Downstream parsing, indexing, or LLM systems may consume extractor output. Keep output stable and normalized; do not add prompt, profile, or app-specific workflow logic here.
- Deployment configuration owns deployed function/IAM/runtime wiring. Changes to deployment targets, function URLs, IAM/auth, package paths, env vars, secrets, or Terraform resources should stay aligned with the relevant setup docs.

## Extraction Rules

- PDF extraction uses `pymupdf4llm.to_markdown` for body text and PDF annotation links for hyperlink discovery.
- DOCX extraction uses Mammoth/BeautifulSoup/Markdownify for body text plus `.rels` inspection for hyperlinks.
- Link extraction should union document hyperlinks with URL extraction from body text, normalize supported HTTP(S) links, and filter `mailto:`, `tel:`, and non-HTTP schemes.
- Email extraction should include body text and raw annotation link URLs.
- Keep output compact: `markdown`, `email_addresses`, `link_urls`, and `phone_numbers`.

## Validation

Before considering changes complete, run the relevant subset of:

```bash
uv run --with ruff ruff check .
./scripts/build-function-zip.sh
```

Run focused local extraction checks when changing PDF parsing, DOCX parsing, URL normalization, phone/email extraction, platform adapters, or package generation.
