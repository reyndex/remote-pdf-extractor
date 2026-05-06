# Remote PDF Extractor

Serverless function that extracts clean markdown plus structured contact info (email addresses, phone numbers, and link URLs) from PDF and DOCX uploads. Returns a JSON object the caller can pass straight to an LLM or to downstream parsing.

Two deployment targets:

- Google Cloud Functions 2nd gen
- AWS Lambda

## Response shape

POST a PDF or DOCX as multipart form field `file`, or provide a generic HTTP(S) download URL in `file_url` as a JSON body or form field. When both are present, the multipart `file` upload is used. Every response is HTTP 200 with a `status` + `data` envelope; clients distinguish by the `status` field.

Direct upload:

```bash
curl --form "file=@document.pdf" "$FUNCTION_URL"
```

Generic download URL:

```bash
curl \
  --header "content-type: application/json" \
  --data '{"file_url":"https://example.com/document.pdf"}' \
  "$FUNCTION_URL"
```

On success, `data` is the extraction object:

```json
{
  "status": "success",
  "data": {
    "markdown": "...",
    "email_addresses": ["foo@bar.com"],
    "link_urls": ["https://github.com/foo"],
    "phone_numbers": ["+15551234567", "3365005405"]
  }
}
```

On failure, `data` is the error message:

```json
{
  "status": "error",
  "data": "Unsupported file: expected PDF or DOCX"
}
```

Phone format: preserve leading `+` only when source contained it; otherwise return digits only with punctuation stripped.

## Extraction pipeline

- **PDF**: `pymupdf4llm.to_markdown` for the body, `pymupdf.page.get_links()` for annotation hyperlinks
- **DOCX**: `mammoth.convert_to_html` → layout-table flatten via `BeautifulSoup` → `markdownify` for the body, plus a zipfile walk over `.rels` for hyperlinks
- **Link URLs**: annotation/zip-rels URIs unioned with `urlextract.find_urls(body)`, normalized to `https://...`, query string stripped, trailing slash stripped, `mailto:`/`tel:`/non-http schemes filtered out
- **Email addresses**: regex over `body + raw annotation link URLs`; the `\b` word boundary strips `mailto:` prefixes naturally
- **Phone numbers**: keep explicit `+` country codes, otherwise keep local numbers without adding a default region; spaces, hyphens, parentheses, and dots are stripped

Format detection is by content signature, not by content type:

- PDF must start with `%PDF-`
- DOCX must be a ZIP archive containing `word/document.xml`

Max upload/download size: 20 MB.

## Repo layout

- `function/` — Shared core (`core.py`) + platform handlers (`gcp_handler.py`, `aws_handler.py`) + entry router (`main.py`)
- `scripts/build-function-zip.sh` — Local package builder for both deployment targets
- `package/` — Committed deployment zips consumed directly by Terraform
- `terraform-gcp/` — GCP Cloud Functions deployment from `package/gcp-cloud-function.zip`
- `terraform-aws/` — AWS Lambda deployment from `package/aws-lambda.zip`
- `docs/` — Setup guides

## Build deployment packages

Run the package builder before Terraform whenever `function/` or `function/requirements.txt` changes:

```bash
./scripts/build-function-zip.sh
```

Commit the generated files under `package/` with the source change. Terraform does not run `pip`, create zip files, or use the archive provider during apply.

## Start here

- [Docs Index](./docs/README.md)
- [GCP Setup Guide](./docs/gcp-setup.md)
- [AWS Setup Guide](./docs/aws-setup.md)
- [Terraform GCP Overview](./terraform-gcp/README.md)
- [Terraform AWS Overview](./terraform-aws/README.md)

## Notes

- GCP uses an authenticated HTTP function with Google IAM + ID-token auth and configurable ingress
- AWS uses a private Lambda Function URL with `AWS_IAM` auth (SigV4)
- The same `function/` source is shipped to both targets; the only platform-specific code lives in `gcp_handler.py` (Flask request adapter) and `aws_handler.py` (Lambda event adapter)

## License

AGPL-3.0. See the upstream [pymupdf4llm license](https://github.com/pymupdf/pymupdf4llm/blob/main/LICENSE).
