# FNOL Insurance Claims Processing System

An AI-powered **First Notice of Loss (FNOL)** document processing backend built with FastAPI and a locally-running LLM via [Ollama](https://ollama.ai). The system ingests ACORD automobile loss notice PDFs, extracts structured fields using an LLM, validates completeness and consistency, and routes each claim to the appropriate handling queue.

---


## Architecture Overview
<img width="1024" height="1536" alt="ChatGPT Image May 10, 2026, 02_02_11 PM" src="https://github.com/user-attachments/assets/dddd54dc-cf90-4d5d-90b8-fa635555f2df" />


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
├── frontend/                    # User-Interface for FNOL Processor
├── .env.example                 # Environment variable template
├── pyproject.toml               # pytest configuration
├── requirements.txt
└── README.md
```

---

## Prerequisites
Python >= 3.11

Ollama

Git

Pip

---

## Setup Instructions

### 1. Install & Run Ollama

Ollama runs a local LLM inference server. It must be running before starting the API.

**macOS:**
```bash
brew install ollama
ollama serve         
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
ollama pull llama3.1
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags   -> this will list available models pulled from ollama
```

---

### 2. Clone & Install Python Dependencies

```bash
git clone https://github.com/Tawheed-tariq/FNOL_processor.git
cd FNOL_processor

# Create a virtual environment
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
OLLAMA_MODEL=llama3.1                
OLLAMA_TIMEOUT=120                  
INVESTIGATION_MIN_CLAIM_AMOUNT=50000 
```

---

## Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is now available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Start UI
```bash
cd frontend
npm run dev
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
