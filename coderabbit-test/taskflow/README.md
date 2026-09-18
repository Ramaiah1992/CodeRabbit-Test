# TaskFlow

A small task-management REST API built with Flask and SQLite. It is deliberately
compact: enough structure to be a real project, small enough to read in one sitting.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
export SECRET_KEY="something-long-and-random"
flask --app wsgi run --debug
```

The API listens on `http://127.0.0.1:5000`.

## Configuration

| Variable             | Default        | Purpose                                  |
| -------------------- | -------------- | ---------------------------------------- |
| `SECRET_KEY`         | `dev-only-...` | HMAC key for session tokens              |
| `DB_PATH`            | `taskflow.db`  | SQLite file location                     |
| `TOKEN_TTL_SECONDS`  | `3600`         | How long an issued token stays valid     |

## API

| Method   | Path                  | Auth | Description                     |
| -------- | --------------------- | ---- | ------------------------------- |
| `GET`    | `/health`             | no   | Liveness probe                  |
| `POST`   | `/api/users/register` | no   | Create an account               |
| `POST`   | `/api/users/login`    | no   | Exchange credentials for a token |
| `GET`    | `/api/tasks`          | yes  | List tasks, paginated           |
| `POST`   | `/api/tasks`          | yes  | Create a task                   |
| `GET`    | `/api/tasks/<id>`     | yes  | Fetch a single task             |
| `PATCH`  | `/api/tasks/<id>`     | yes  | Update title/status/priority    |
| `DELETE` | `/api/tasks/<id>`     | yes  | Delete a task                   |

Authenticated requests carry `Authorization: Bearer <token>`.

## Tests

```bash
pytest
```

## Layout

```
app/
  __init__.py      application factory
  config.py        configuration defaults
  db.py            connection handling and schema
  models.py        Task and User records
  auth.py          password hashing, token issue/verify
  routes/
    users.py       registration and login
    tasks.py       task CRUD
tests/             pytest suite
```
