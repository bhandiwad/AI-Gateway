# File Guardrails

The AI Gateway can apply guardrails to file content, including PDFs, Word documents, images, and more. This ensures that sensitive information in uploaded files is detected and handled according to your security policies.

## Overview

When users send files (images, documents) in chat messages or upload files directly, the system can:

1. **Extract text content** from various file formats
2. **Apply guardrail processors** (PII detection, secrets scanning, compliance checks)
3. **Block or redact** content that violates policies

## Supported File Types

| File Type | Extensions | Extraction Method |
|-----------|------------|-------------------|
| PDF | `.pdf` | PyPDF2 text extraction |
| Word Documents | `.docx` | python-docx text extraction |
| Plain Text | `.txt` | Direct text reading |
| CSV | `.csv` | Direct text reading |
| JSON | `.json` | Direct text reading |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | OCR (pytesseract) |

## How It Works

### Automatic Scanning in Chat

When a user sends an image in a chat completion request (via base64 or URL), the system automatically:

1. Detects image content in the message
2. Extracts text using OCR
3. Applies the active guardrail profile
4. Blocks the request if violations are found

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What's in this document?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ]
}
```

If the image contains sensitive content (PII, secrets, etc.), the request will be blocked:

```json
{
  "error": "File content blocked: PII detected: email, phone. Request blocked for compliance."
}
```

### Manual File Scanning API

Scan files before sending them to chat:

#### Upload File Scan

```bash
POST /api/v1/admin/guardrails/scan-file
Authorization: Bearer YOUR_TOKEN
Content-Type: multipart/form-data

file: (binary file content)
profile_id: (optional) guardrail profile ID
```

**Response:**
```json
{
  "passed": false,
  "message": "PII detected: email, ssn. Request blocked for compliance.",
  "action": "block",
  "file_name": "document.pdf",
  "file_type": "application/pdf",
  "extracted_text_preview": "John Doe, email: john@example.com, SSN: 123-45-6789...",
  "detected_issues": [
    {
      "processor": "pii_detection",
      "action": "block",
      "message": "PII detected: email, ssn"
    }
  ],
  "redacted_content": null
}
```

#### Base64 Content Scan

```bash
POST /api/v1/admin/guardrails/scan-base64
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "content": "base64-encoded-file-content",
  "content_type": "application/pdf",
  "filename": "document.pdf",
  "profile_id": 1
}
```

**Response:**
```json
{
  "passed": true,
  "message": "File passed all guardrail checks",
  "action": "allow",
  "file_type": "application/pdf",
  "extracted_text_preview": "This is a clean document with no sensitive data...",
  "detected_issues": null
}
```

## Guardrail Processors Applied

All configured guardrail processors in your profile are applied to file content:

| Processor | What It Detects |
|-----------|-----------------|
| `pii_detection` | Email, phone, SSN, Aadhaar, PAN, credit cards |
| `secrets_detection` | API keys, tokens, passwords, connection strings |
| `prompt_injection` | Malicious prompts embedded in documents |
| `dpdp_compliance` | DPDP Act (India) violations |
| `gdpr_compliance` | GDPR violations |
| `hipaa_compliance` | Healthcare data violations |
| `pci_dss_compliance` | Payment card data |
| `code_detection` | Source code in documents |
| `toxicity_filter` | Harmful content |

## Configuration

### Enable File Scanning

File scanning is enabled by default when guardrail profiles are configured. No additional configuration is required.

### OCR Dependencies

For image OCR to work, ensure these are installed (included in Docker image):

```bash
# System packages (in Dockerfile)
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Python packages (in pyproject.toml)
pytesseract>=0.3.10
Pillow>=10.0.0
```

### PDF/DOCX Dependencies

```bash
# Python packages (in pyproject.toml)
PyPDF2>=3.0.0
python-docx>=1.1.0
```

## Actions

Configure what happens when violations are detected:

| Action | Behavior |
|--------|----------|
| `block` | Reject the request entirely |
| `redact` | Replace sensitive content with `[REDACTED]` |
| `warn` | Allow but log the violation |

## Example Use Cases

### 1. Prevent PII in Document Analysis

A user uploads a contract for analysis. The system detects SSN and phone numbers:

```
Request: "Summarize this contract"
File: contract.pdf (contains SSN: 123-45-6789)
Result: BLOCKED - "PII detected: ssn, phone"
```

### 2. Block Secrets in Code Screenshots

A developer shares a screenshot of their code. OCR detects an API key:

```
Request: "Help me debug this code"
File: screenshot.png (contains OPENAI_API_KEY=sk-...)
Result: BLOCKED - "Secrets detected: api_key"
```

### 3. Pre-scan Documents Before Upload

An application pre-scans documents before allowing upload:

```bash
# Scan the file first
curl -X POST "http://localhost:8000/api/v1/admin/guardrails/scan-file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# If passed, proceed with chat
if [ "$passed" = "true" ]; then
  # Send to chat API
fi
```

## Logging

All file scans are logged for audit:

```json
{
  "event": "file_guardrail_check",
  "file_type": "application/pdf",
  "file_name": "document.pdf",
  "passed": false,
  "triggered_processor": "pii_detection",
  "action": "block",
  "tenant_id": 1
}
```

## Limitations

1. **OCR Accuracy** - Image text extraction depends on image quality
2. **Encrypted PDFs** - Cannot extract text from password-protected files
3. **Complex Layouts** - Tables and multi-column layouts may not extract perfectly
4. **File Size** - Large files may take longer to process
5. **Language Support** - OCR currently supports English (add more language packs as needed)

## Troubleshooting

### OCR Not Working

Check that tesseract is installed:
```bash
docker exec ai-gateway-backend-1 tesseract --version
```

### PDF Extraction Empty

Check PyPDF2 is installed:
```bash
docker exec ai-gateway-backend-1 pip list | grep PyPDF2
```

### DOCX Extraction Empty

Check python-docx is installed:
```bash
docker exec ai-gateway-backend-1 pip list | grep python-docx
```
