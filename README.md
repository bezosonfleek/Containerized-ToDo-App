# 📦 Todo API — Containerized with Docker + FastAPI + PostgreSQL

A learning project that teaches core Docker concepts through a real REST API.

---

## 🗂 Project Structure

```
todo-app/
├── app/
│   └── main.py          # FastAPI application
├── Dockerfile           # How to build the API image
├── docker-compose.yml   # Orchestrates api + db containers
└── requirements.txt     # Python dependencies
```

---

## 🚀 Running the App

```bash
# Build and start both containers
docker compose up --build

# Run in background (detached mode)
docker compose up --build -d

# Stop everything
docker compose down

# Stop AND delete the database volume (fresh start)
docker compose down -v
```

API is live at: **http://localhost:8000**  
Interactive docs at: **http://localhost:8000/docs**

---

## 🧪 Testing the API

### Create a todo
```bash
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Docker", "description": "Containers are cool"}'
```

### List all todos
```bash
curl http://localhost:8000/todos
```

### Mark as completed
```bash
curl -X PATCH http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### Delete a todo
```bash
curl -X DELETE http://localhost:8000/todos/1
```

---

## 🧠 What You're Learning

| Concept | Where it appears |
|---|---|
| **Dockerfile** | Building a custom image from `python:3.12-slim` |
| **Layers & caching** | Copying `requirements.txt` before source code |
| **Port mapping** | `"8000:8000"` in docker-compose |
| **Environment variables** | DB credentials passed via `environment:` |
| **Named volumes** | `postgres_data` persists DB between restarts |
| **Bind mounts** | `./app:/app/app` enables live code reload |
| **Health checks** | API waits for Postgres to be ready before starting |
| **Service networking** | API connects to `db` hostname (Docker's internal DNS) |

---

## 🔍 Useful Docker Commands

```bash
# See running containers
docker ps

# View logs for the API container
docker compose logs api

# Follow logs in real time
docker compose logs -f api

# Open a shell inside the API container
docker compose exec api bash

# Connect to Postgres directly
docker compose exec db psql -U postgres -d todos

# See all images on your machine
docker images

# Remove unused images/containers/volumes
docker system prune
```

---

## ➡️ Next Steps

Once you're comfortable here, try:
1. **Add a `.env` file** — move secrets out of `docker-compose.yml`
2. **Add a second stage** to the Dockerfile (multi-stage build) to make the image smaller
3. **Scale the API** — `docker compose up --scale api=3` (add a load balancer)
4. **Add Redis** — cache the `/todos` list response
