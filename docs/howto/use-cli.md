<!-- SPDX-FileCopyrightText: 2026 Georges Martin <jrjsmrtn@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# How to Use the CLI

Recipes for building, inspecting, verifying, and extracting `.jxz` containers from the command line.

## Build a container

Create a basic unsigned container from a JUnit XML report:

```bash
jxz build report.xml --created-by "pytest-jux/0.1.0" --report-type pytest-junit
```

This produces `report.jxz` alongside the input file.

## Build with attachments

Attach files to the container. Use `PATH:TEST_ID` to associate an attachment with a specific test:

```bash
jxz build report.xml \
    --created-by "pytest-jux/0.1.0" \
    --report-type pytest-junit \
    --attachment screenshot.png:test_login \
    --attachment trace.json \
    -o output/report.jxz
```

## Build a signed container

Sign the container with a private key and certificate:

```bash
jxz build report.xml \
    --created-by "pytest-jux/0.1.0" \
    --report-type pytest-junit \
    --key signer.pem \
    --cert signer-cert.pem \
    -o signed-report.jxz
```

## Build with metadata

Add extra files under `META-INF/`:

```bash
jxz build report.xml \
    --created-by "pytest-jux/0.1.0" \
    --report-type pytest-junit \
    --meta pytest-metadata.json \
    --meta environment.json
```

## Build with a fixed timestamp

Useful for reproducible builds in CI:

```bash
jxz build report.xml \
    --created-by "ci-pipeline/2.0" \
    --report-type pytest-junit \
    --timestamp "2026-01-15T10:30:00+00:00"
```

## Sign an existing container

Sign an unsigned container in-place:

```bash
jxz sign report.jxz --key signer.pem
```

## Sign with a certificate

```bash
jxz sign report.jxz --key signer.pem --cert signer-cert.pem
```

## Sign to a different file

```bash
jxz sign report.jxz --key signer.pem -o signed-report.jxz
```

## Re-sign a container

Replace an existing signature with a new one:

```bash
jxz sign signed-report.jxz --key new-key.pem --cert new-cert.pem --force
```

## Build-then-sign pipeline

Build unsigned in CI, sign separately by a trusted authority:

```bash
jxz build report.xml --created-by "ci/2.0" --report-type pytest-junit -o report.jxz
jxz sign report.jxz --key authority.pem --cert authority-cert.pem
```

## Inspect a container

Human-readable summary:

```bash
jxz inspect report.jxz
```

```
Container: report.jxz
  Created-By:  pytest-jux/0.1.0
  Report-Type: pytest-junit
  Timestamp:   2026-01-15T10:30:00+00:00
  Signed:      Yes (RSA-SHA256)

Files (2):
  Name                                       Size   SHA-256
  junit.xml                                 4.5 KB   7d865e95...
  attachments/screenshot.png               44.2 KB   e3b0c442...
```

## Inspect with JSON output

```bash
jxz inspect --json report.jxz
```

```json
{
  "file": "report.jxz",
  "created_by": "pytest-jux/0.1.0",
  "report_type": "pytest-junit",
  "timestamp": "2026-01-15T10:30:00+00:00",
  "signed": true,
  "signature": "Yes (RSA-SHA256)",
  "files": [
    {"name": "junit.xml", "size": 4521, "sha256": "7d865e95..."}
  ]
}
```

## Verify container integrity

Basic verification (digests, and signature if present):

```bash
jxz verify report.jxz
```

```
OK
```

Exit code is 0 on success, 1 on failure.

## Verify with a certificate

```bash
jxz verify --cert signer.pem report.jxz
```

## Verify in quiet mode

Suppress output on success — useful in scripts where you only check the exit code:

```bash
jxz verify --quiet report.jxz && echo "passed" || echo "failed"
```

## Verify with JSON output

```bash
jxz verify --json report.jxz
```

```json
{"status": "ok", "message": "Verification passed"}
```

On failure:

```json
{"status": "error", "message": "Digest mismatch for junit.xml: expected abc..., got def..."}
```

## Extract all contents

```bash
jxz extract report.jxz -o output/
```

Prints each extracted path:

```
output/junit.xml
output/attachments/screenshot.png
output/META-INF/pytest-metadata.json
```

## Extract report only

```bash
jxz extract --report-only report.jxz -o output/
```

```
output/junit.xml
```

## Extract attachments only

```bash
jxz extract --attachments-only report.jxz -o output/
```

```
output/attachments/screenshot.png
output/attachments/trace.json
```

## Use in scripts

Extract the creator from a container using `jq`:

```bash
jxz inspect --json report.jxz | jq -r '.created_by'
```

Check whether a container is signed:

```bash
jxz inspect --json report.jxz | jq '.signed'
```

List file names and sizes:

```bash
jxz inspect --json report.jxz | jq -r '.files[] | "\(.name)\t\(.size)"'
```

Batch-verify a directory of containers:

```bash
for f in reports/*.jxz; do
    if jxz verify --quiet "$f"; then
        echo "OK: $f"
    else
        echo "FAIL: $f"
    fi
done
```

## Run as a Python module

If the `jxz` console script is not on your `PATH`, use the module form:

```bash
python -m jxz build report.xml --created-by "tool/1.0" --report-type pytest-junit
python -m jxz sign report.jxz --key signer.pem
python -m jxz inspect report.jxz
python -m jxz verify --json report.jxz
python -m jxz extract -o output/ report.jxz
```
