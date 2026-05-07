# 🚗 FNOL Insurance Claims Processing System

An AI-powered **First Notice of Loss (FNOL)** document processing backend built with FastAPI and a locally-running LLM via [Ollama](https://ollama.ai). The system ingests ACORD automobile loss notice PDFs, extracts structured fields using an LLM, validates completeness and consistency, and routes each claim to the appropriate handling queue — all through a clean RESTful API.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Folder Structure](#folder-structure)
3. [Prerequisites](#prerequisites)
4. [Setup Instructions](#setup-instructions)
   - [Install & Run Ollama](#1-install--run-ollama)
   - [Clone & Install Python Dependencies](#2-clone--install-python-dependencies)
   - [Configure Environment Variables](#3-configure-environment-variables)
5. [Running the Server](#running-the-server)
6. [API Reference](#api-reference)
   - [Health Check](#get-apiv1health)
   - [Readiness Check](#get-apiv1healthready)
   - [Process Single Claim](#post-apiv1claimsprocess)
   - [Batch Process Claims](#post-apiv1claimsbatch)
   - [Supported Routes](#get-apiv1claimssupported-routes)
7. [Example Requests & Responses](#example-requests--responses)
8. [Routing Logic](#routing-logic)
9. [Running Tests](#running-tests)
10. [Extending the System](#extending-the-system)

---

## Architecture Overview

```
PDF Upload
    │
    ▼
┌─────────────────────┐
│  Document Ingestion  │  pdfplumber: validates, extracts text + tables
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   LLM Extraction    │  Ollama (llama3/mistral): prompt-based JSON extraction
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Validation Service  │  Domain rules: required fields, dates, VIN, estimates
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Routing Engine    │  Rule-based: Fast-track / Manual / Investigation / Specialist
└─────────┬───────────┘
          │
          ▼
   Structured JSON Response (ClaimProcessingResponse)
```

### Processing Pipeline

Each claim goes through four sequential stages:

| Stage | Component | Technology |
|-------|-----------|------------|
| **Ingestion** | `DocumentIngestionService` | pdfplumber |
| **Extraction** | `LLMExtractionService` | Ollama REST API |
| **Validation** | `ValidationService` | Pydantic + domain rules |
| **Routing** | `RoutingEngine` | Rule engine |

### Design Principles

- **Separation of concerns** — each pipeline stage is an isolated, testable service class
- **Dependency injection** — FastAPI `Depends()` wires services; easy to swap implementations
- **Environment-driven config** — all tuneable parameters live in `.env` / `Settings`
- **Fail gracefully** — LLM parse failures return a partial claim rather than crashing
- **Stateless services** — safe for horizontal scaling behind a load balancer
- **Thread-pool offloading** — LLM calls run in a thread pool, keeping the async event loop free

---

## Folder Structure

```
fnol_processor/
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, router registration
│   ├── api/
│   │   ├── dependencies.py      # FastAPI dependency providers (DI)
│   │   └── routes/
│   │       ├── claims.py        # POST /process, POST /batch, GET /supported-routes
│   │       └── health.py        # GET /health, GET /health/ready
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings, env var driven)
│   │   ├── exceptions.py        # Domain exception hierarchy
│   │   └── logging_config.py    # Structured stdout logging
│   ├── models/
│   │   └── schemas.py           # ALL Pydantic v2 models (request, response, domain)
│   └── services/
│       ├── ingestion.py         # PDF validation + text extraction
│       ├── extraction.py        # Ollama LLM prompt + JSON parsing
│       ├── validation.py        # Field-level domain validation
│       ├── routing.py           # Rule-based routing engine
│       └── processor.py        # Orchestrator: ties all 4 stages together
├── tests/
│   ├── conftest.py              # Shared fixtures, mock processor
│   ├── unit/
│   │   ├── test_ingestion.py    # DocumentIngestionService tests
│   │   ├── test_extraction.py   # LLMExtractionService tests
│   │   ├── test_validation.py   # ValidationService tests
│   │   └── test_routing.py      # RoutingEngine tests
│   └── integration/
│       └── test_api.py          # FastAPI endpoint tests (TestClient)
├── .env.example                 # Environment variable template
├── pyproject.toml               # pytest configuration
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Python | 3.11+ | Runtime |
| pip | 23+ | Package installation |
| Ollama | 0.1.32+ | Local LLM server |
| Git | any | Clone repository |

---

## Setup Instructions

### 1. Install & Run Ollama

Ollama runs a local LLM inference server. It must be running before starting the API.

**macOS:**
```bash
brew install ollama
ollama serve          # start the server (keep this terminal open)
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

**Windows:**
Download the installer from [https://ollama.ai/download](https://ollama.ai/download).

**Pull your chosen model** (in a new terminal):
```bash
# Recommended – good quality + speed balance
ollama pull llama3

# Alternatives
ollama pull mistral
ollama pull phi3
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
# Should list your pulled models
```

---

### 2. Clone & Install Python Dependencies

```bash
git clone <your-repo-url>
cd fnol_processor

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` to match your environment. Key settings:

```env
OLLAMA_MODEL=llama3                  # Must match what you pulled
OLLAMA_TIMEOUT=120                   # Increase for slower machines
INVESTIGATION_MIN_CLAIM_AMOUNT=50000 # USD threshold for investigation routing
```

---

## Running the Server

```bash
# Development (auto-reload on code changes)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API is now available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## API Reference

### `GET /api/v1/health`
Basic liveness check. Always returns 200 if the Python process is alive.

**Response:**
```json
{ "status": "ok", "version": "1.0.0" }
```

---

### `GET /api/v1/health/ready`
Readiness check — verifies Ollama is reachable and lists available models.

| Code | Meaning |
|------|---------|
| 200 | Ready — Ollama reachable |
| 503 | Degraded — Ollama unreachable |

---

### `POST /api/v1/claims/process`
Process a **single** FNOL PDF document.

**Request:** `multipart/form-data`
- `file` (required): PDF file, max 20 MB

**Response:** `ClaimProcessingResponse` (see schema below)

---

### `POST /api/v1/claims/batch`
Process **up to 10** FNOL PDFs in a single request.

**Request:** `multipart/form-data`
- `files` (required): 1–10 PDF files

**Response:** `BatchProcessingResponse`

---

### `GET /api/v1/claims/supported-routes`
List all routing categories with descriptions and typical SLAs.

---

## Example Requests & Responses

### Process a Single Claim

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/claims/process \
  -F "file=@ACORD-Automobile-Loss-Notice.pdf" \
  | python -m json.tool
```

**Response:**
```json
{
  "claim_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "success",
  "extracted_claim": {
    "policy": {
      "policy_number": "PA-123456789",
      "carrier": "State Farm Insurance",
      "naic_code": "25143",
      "line_of_business": "Auto",
      "agency_name": "ABC Insurance Agency",
      "agency_code": null
    },
    "insured": {
      "name": "John Michael Doe",
      "date_of_birth": "03/22/1985",
      "mailing_address": "123 Main Street, Springfield, IL 62701",
      "primary_phone": "217-555-0123",
      "email": null
    },
    "incident": {
      "date_of_loss": "01/14/2024",
      "time_of_loss": "3:30 PM",
      "location_street": "400 E Oak Avenue",
      "location_city_state_zip": "Springfield, IL 62702",
      "police_contacted": true,
      "report_number": "SPD-2024-00123",
      "description": "Insured was travelling northbound on Oak Avenue when a red sedan ran a stop sign and struck the insured's vehicle on the driver's side door.",
      "incident_type": "Collision"
    },
    "vehicle": {
      "year": "2021",
      "make": "Toyota",
      "model": "Camry",
      "vin": "4T1BF1FK5CU123456",
      "estimate_amount": 8500.0,
      "damage_description": "Driver side door severely dented, window shattered, airbag deployed."
    }
  },
  "validation": {
    "is_valid": true,
    "missing_required_fields": [],
    "issues": [
      {
        "field": "vehicle.vin",
        "severity": "warning",
        "message": "VIN '4T1BF1FK5CU123456' does not match the standard 17-character format."
      }
    ],
    "completeness_score": 0.821
  },
  "routing": {
    "route": "Manual Review",
    "reasoning": "Routed to Manual Review because: data completeness score is 82%, moderate damage estimate requires adjuster sign-off.",
    "priority_score": 5,
    "flags": []
  },
  "metadata": {
    "filename": "ACORD-Automobile-Loss-Notice.pdf",
    "file_size_bytes": 124503,
    "pages_extracted": 4,
    "characters_extracted": 3847,
    "processing_time_ms": 8234.5,
    "llm_model": "llama3",
    "processed_at": "2024-01-15T10:30:00Z"
  }
}
```

### Batch Processing

```bash
curl -X POST http://localhost:8000/api/v1/claims/batch \
  -F "files=@claim1.pdf" \
  -F "files=@claim2.pdf" \
  | python -m json.tool
```

**Response:**
```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "items": [
    { "filename": "claim1.pdf", "claim_id": "...", "status": "success", "response": { ... } },
    { "filename": "claim2.pdf", "claim_id": "...", "status": "success", "response": { ... } }
  ],
  "batch_processing_time_ms": 16820.3
}
```

---

## Routing Logic

Claims are evaluated against rules in priority order:

| Route | Triggers |
|-------|---------|
| **Investigation** | Theft/Hit-and-Run, damage ≥ $50k, vehicle used without permission, severe data inconsistency |
| **Specialist Queue** | Bodily injuries, fire/flood/natural disaster, child seat damage, 2+ third-party vehicles |
| **Manual Review** | ≥3 missing required fields, validation errors, completeness < 45% |
| **Fast-track** | All required fields present, no injuries, low-moderate estimate, clean validation |

The `reasoning` string in every response explains exactly why a route was chosen, and `flags` lists all notable signals detected.

---

## Running Tests

The test suite requires **no running Ollama instance** — the `ClaimsProcessor` is mocked.

```bash
# All tests
pytest

# With verbose output
pytest -v

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# A specific test file
pytest tests/unit/test_validation.py -v

# A specific test
pytest tests/unit/test_routing.py::TestInvestigation::test_theft_routes_to_investigation -v

# With coverage report
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

**Test coverage areas:**

| Module | Test File | Coverage |
|--------|-----------|----------|
| `ingestion.py` | `unit/test_ingestion.py` | File type, size limits, extraction, tables, multi-page |
| `extraction.py` | `unit/test_extraction.py` | JSON parsing, markdown stripping, error handling, retries |
| `validation.py` | `unit/test_validation.py` | Required fields, dates, VIN, estimates, child seat |
| `routing.py` | `unit/test_routing.py` | All 4 routes, flags, priority scores, edge cases |
| API endpoints | `integration/test_api.py` | All endpoints, error codes, response shapes |

---

## Extending the System

### Add a New LLM Provider (e.g. OpenAI)

1. Create `app/services/extraction_openai.py` implementing the same `extract(document) -> ExtractedClaim` interface
2. Update `app/services/processor.py` to inject the new service based on a config flag

### Add OCR Support for Scanned PDFs

Install `pytesseract` + Tesseract and add a pre-processing step in `DocumentIngestionService._extract_text()` that falls back to OCR when pdfplumber returns empty text.

### Persist Results to a Database

Add SQLAlchemy models under `app/db/` and call `db.save(result)` in `ClaimsProcessor.process()`. Use FastAPI's `Depends()` to inject a database session.

### Add Authentication

Use FastAPI's `HTTPBearer` or `OAuth2PasswordBearer` dependency on the `/claims/*` routes.

### Frontend Integration

The API is CORS-enabled and fully documented via OpenAPI. Any frontend (React, Vue, etc.) can:
1. `POST /api/v1/claims/process` with a `FormData` object
2. Render the structured `ClaimProcessingResponse` JSON

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t fnol-processor .
docker run -p 8000:8000 --env-file .env fnol-processor
```

> **Note:** Ollama must be accessible from the container. Use `host.docker.internal` as `OLLAMA_BASE_URL` on Mac/Windows, or run Ollama in a separate container on the same Docker network.