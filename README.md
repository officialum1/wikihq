# Wikipedia Platform

A complete Wikipedia mirror and editable wiki platform using Next.js 14, FastAPI, PostgreSQL 15, Redis, Elasticsearch, and a Python import worker.

## Folder Structure

```text
wikipedia-platform/
├── frontend/
├── backend/
├── worker/
├── render.yaml
└── docker-compose.yml
```

## Local Development

```bash
docker compose up --build
```

The frontend runs on `http://localhost:3000`, the API on `http://localhost:8000`, PostgreSQL on `localhost:5432`, Redis on `localhost:6379`, and Elasticsearch on `localhost:9200`.

## Required Environment Variables

### Frontend

| Variable | Purpose | Local value |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Browser-accessible FastAPI base URL | `http://localhost:8000` |
| `INTERNAL_API_URL` | Server-side FastAPI base URL for Next.js rendering | `http://api:8000` |
| `INTERNAL_API_HOSTPORT` | Render private `host:port` for the API when `INTERNAL_API_URL` is not set | unset locally |

### Backend API

| Variable | Purpose | Local value |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://wiki:wiki@postgres:5432/wikipedia` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://elasticsearch:9200` |
| `JWT_SECRET` | Secret used to sign JWT access tokens | `local-development-jwt-secret-change-before-production` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes | `1440` |
| `CORS_ORIGINS` | Allowed browser origins, comma separated | `http://localhost:3000` |
| `ADMIN_BOOTSTRAP_USERNAME` | Optional first admin username | `admin` |
| `ADMIN_BOOTSTRAP_EMAIL` | Optional first admin email | `admin@wikihq.local` |
| `ADMIN_BOOTSTRAP_PASSWORD` | Optional first admin password | `admin12345` |

### Worker

| Variable | Purpose | Local value |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://wiki:wiki@postgres:5432/wikipedia` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://elasticsearch:9200` |
| `WIKIPEDIA_DUMP_URL` | Wikipedia XML dump URL | `https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2` |
| `DUMP_PATH` | Local path for the downloaded dump | `/data/enwiki-latest-pages-articles.xml.bz2` |
| `BATCH_SIZE` | Number of articles inserted per batch | `1000` |
| `RUN_ONCE` | Exit after one import pass when `true` | `false` |
| `REFRESH_INTERVAL_SECONDS` | Delay before the worker checks again | `86400` |

## API

- `GET /api/article/{title}`
- `GET /api/search?q={query}&page={n}`
- `GET /api/progress`
- `POST /api/article`
- `PUT /api/article/{id}`
- `GET /api/article/{id}/history`
- `POST /api/auth/register`
- `POST /api/auth/login`
