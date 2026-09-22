# Remote PDF Extractor — agent rules

Use the [local documentation rules](docs/guidelines/README.md) for source verification, instruction parity, and shared-policy maintenance.

Read [README.md](README.md) for the public contract and the relevant [AWS](docs/aws-setup.md) or [GCP](docs/gcp-setup.md) guide for deployment.

- This is a reusable extraction service. Keep caller business rules, persistence, authorization decisions, and LLM orchestration outside it.
- Preserve envelopes, request IDs, multipart-over-URL priority, signature-based formats, 20 MB limit, and contact/link normalization in README. Contract changes require caller review.
- Shared extraction belongs in `function/extractor/`; platform adapters are `aws_handler.py` and `gcp_handler.py`. Use owned constants for closed internal states without abstracting every external wire value.
- Never log secrets, signed URLs, documents, extracted text, or contact/source data.
- Build and commit consumed `package/` artifacts after runtime/dependency changes. Keep AWS `us-west-2` and GCP `us-west1` defaults.

## Request journey and source map

`function/main.py` exposes platform entry points backed by `function/aws_handler.py` and `function/gcp_handler.py`. The adapters translate Lambda or Flask requests into shared extraction inputs and standard responses. `function/extractor/request_payload.py` parses JSON/form/multipart input; `remote_file.py` downloads URL input; `core.py` owns document parsing and normalization. Response schemas, errors, constants, and closed states have separate owning modules.

A request selects an uploaded file before considering a URL. URL input downloads bytes under a size limit. Shared extraction validates content signature, parses PDF or DOCX, derives markdown and contact/link values, and returns the compact extraction object. Adapters attach request identity and status. Preserve the same public behavior across platforms while keeping platform transport handling outside the extraction core.

Read only the relevant deployment guide for platform changes. Both Terraform roots consume archives built from the same source, so shared dependency or core changes affect both targets even if testing started with only one provider. Do not introduce a provider-specific extraction result unless the public contract intentionally changes.

## File and download boundaries

The application limit is 20 MB of input bytes. URL downloads validate HTTP(S) schemes, check declared content length when available, and count streamed chunks so absent or dishonest headers cannot bypass the limit. The downloader also validates the final response URL's scheme. These checks are not a claim of comprehensive private-network or DNS-rebinding protection; do not describe them as such without implementing and verifying that behavior.

The current downloader uses bounded chunks and a 30-second timeout. Keep failures distinguishable from unsupported document format. Never print signed URLs, response bodies, or downloaded content while diagnosing a failure. Remote input is caller-provided and must not become a source of credentials or application authorization.

File type comes from signature, not extension or declared MIME type. PDF begins with its expected signature; DOCX must be a ZIP containing the expected document structure. DOCX extraction also has an uncompressed-size limit to bound archive expansion. Preserve that guard when changing ZIP traversal, link relationships, or markdown conversion. Corrupt input should produce the documented application error instead of escaping as an unhandled platform failure.

AWS Function URL synchronous payload limits apply before this application sees uploaded bytes. The 20 MB application limit therefore does not promise a 20 MB direct AWS upload. Use URL input for larger AWS files within the application limit. GCP ingress/authentication constraints are separate from extraction size policy.

## Output and normalization

Successful responses contain markdown, email addresses, link URLs, and phone numbers inside `{ok, data, error}`; failures have null data and a structured error. Request traceability is the response header, not an extra top-level metadata object. Malformed requests/unsupported or corrupt files use HTTP 400; unexpected processing errors use 500.

PDF body text uses PyMuPDF markdown extraction and annotation links. DOCX body text passes through Mammoth, BeautifulSoup layout processing, and Markdownify, with relationship files supplying hyperlinks. Link discovery combines document hyperlinks with body URLs and applies the existing HTTP(S) normalization; `mailto:`, `tel:`, and other non-HTTP schemes are filtered out of `link_urls`. Email discovery includes body text and raw annotation links. Preserve these sources when refactoring so a clickable contact does not disappear just because it was absent from visible text.

Phone output preserves a leading plus only when present in the source; otherwise it returns stripped digits without inventing a default country. This is extractor normalization, not evidence of an E.164 candidate phone. Candidate ownership, semantic classification, and downstream profile decisions belong to callers.

## Packaging constraints

`scripts/build-function-zip.sh` produces both AWS and GCP archives. AWS includes runtime source at root with installed dependencies under `_deps/`; GCP carries source/requirements and copied wheels under `_vendor/`. Terraform consumes these packages directly and does not install dependencies or create archives during apply.

The builder supports AWS Python 3.12/3.13 and ARM64/x86_64 package targets; the GCP path is Python 3.13 with x86_64 wheels. Inspect the builder and Terraform together before changing runtime or architecture. Running the build mutates generated artifacts, so reserve it for source/dependency or packaging changes and include the consumed results in the handoff.

`scripts/package_archive.py` owns archive construction. Keep caches and local virtual environments out of packages. A package that builds on the developer machine can still fail in Lambda or Cloud Build if the wheel platform differs. Verify archive layout and dependency compatibility rather than assuming a local import proves deployment.

## Deployment and integration checks

AWS deploys an IAM-authenticated Function URL. Invocation requires SigV4 and both function/URL invocation permissions; public reachability is not public authorization. Optional VPC attachment changes outbound networking and may require NAT or endpoints. GCP uses ID-token authentication with the function URL as audience and configurable ingress; stricter ingress must match the caller path.

Use the existing setup commands and configuration in the selected Terraform root. Do not broaden roles, disable auth, or change regions merely to make a local example work. If changed configuration requires a caller update, document that dependency explicitly. Keep secrets outside source and Terraform state outside Git.

Do not require both cloud deployments for a prose edit. Keep public examples generic and avoid real candidate data.

## Validation

Follow the [testing policy](docs/guidelines/reyndex-testing-guidelines.md): a test must protect a plausible consequential product failure and add distinct protection.

This repo has no automated test suite today: there is no `tests/` directory and no test runner configuration. Lint config is `pyproject.toml` ruff (`E,F,I`, line 88, target `py311`); `--no-project` is required because there is no `[project]` table. `uv run --no-project --with ruff ruff check .` is the only repository check, and `./scripts/build-function-zip.sh` is required after runtime/dependency changes. No CI is configured in this repo; the listed commands are the only gates. Verification for a parser/adapter change is focused manual exercise of the handler against representative PDF/DOCX input plus a package rebuild; report the platform or live-auth proof that remains unperformed. Documentation-only changes need link checks and `AGENTS.md`/`CLAUDE.md` parity.

The consequential risks here are unbounded downloads, unsafe archive expansion, lost-document/contact regressions, broken platform envelopes, and packaging. Introducing a test runner is a deliberate decision to make only when a change creates such a risk under the local testing policy's admission rule, never a per-change default.
