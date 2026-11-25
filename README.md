# Job-Market-Intelligence-api

An automated job data intelligence platform that collects job postings from multiple sources, normalizes job data, detects duplicates, and stores structured job information for further analysis.

## Tech Stack

- **Backend:** FastAPI
- **Language:** Python 3.12+
- **Package Manager:** uv
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy (Async)
- **Migrations:** Alembic
- **Workflow Orchestration:** Prefect
- **Object Storage:** AWS S3
- **HTTP Client:** HTTPX

## Project Structure

```text
app/
├── adapters/       # External job source integrations
├── api/            # FastAPI routes
├── core/           # Configuration and constants
├── db/             # Database connection management
├── models/         # SQLAlchemy models
├── pipelines/      # Prefect ingestion flows and tasks
├── repositories/   # Database operations
├── schemas/        # Pydantic schemas
├── services/       # Business logic
└── utils/          # Reusable utilities
```

## Prerequisites

- Python 3.12+
- uv
- PostgreSQL
- AWS account with an S3 bucket
- Prefect 3

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/interloid/job-market-intelligence.git
cd job-market-intelligence
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root.

Configure the required database, AWS S3, and application settings according to the project's environment configuration.

Never commit `.env` or AWS credentials to Git.

## Database Migrations

Run all pending migrations:

```bash
uv run alembic upgrade head
```

Generate a new migration:

```bash
uv run alembic revision --autogenerate -m "migration description"
```

Apply the migration:

```bash
uv run alembic upgrade head
```

## Running FastAPI

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Running Prefect Flows

Start the local Prefect server:

```bash
uv run prefect server start
```

Configure the local Prefect API:

```bash
uv run prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
```

Run the required flow using its Python entry point:

```bash
uv run python -m <flow_module>
```

Alternatively, execute the flow through its configured deployment.

## Deploying Prefect Flows

Create a Prefect work pool:

```bash
uv run prefect work-pool create <pool-name> --type process
```

Deploy a flow:

```bash
uv run prefect deploy <flow-file.py>:<flow-function> \
    --name <deployment-name> \
    --pool <pool-name>
```

Start a worker:

```bash
uv run prefect worker start --pool <pool-name>
```

The worker executes scheduled flow runs from the configured work pool.

For production deployments, configure the Prefect API URL, environment variables, database access, and AWS credentials appropriately.
