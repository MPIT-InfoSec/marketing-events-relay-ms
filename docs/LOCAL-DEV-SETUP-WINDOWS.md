# Local Dev Setup (Windows)

## Prerequisites

- Python 3.11+
- Docker Desktop
- Git

## Start MySQL Only (Docker)

```bash
docker compose up -d db
```

## Create venv and Install Deps

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Configure Environment

```bash
copy .env.example .env
```

Edit `.env` and set:

```
DATABASE_URL=mysql+aiomysql://root:password@127.0.0.1:3306/marketing_events_relay
ENCRYPTION_KEY=<your_44_char_fernet_key>
```

Generate a key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Run Migrations

```bash
alembic upgrade head
```

## Start API

```bash
uvicorn app.main:app --reload
```

## Start Worker (new terminal)

```bash
venv\Scripts\activate
python -m app.workers.retry_worker
```
