# 📦 Todo API - Containerized with Docker + FastAPI + PostgreSQL

A learning project that teaches core Docker concepts through a real REST API.

---

## 🔧 Git Setup (do this first)

Before anything else, put this project under version control so you can track your changes as you learn.

```bash
# 1. Initialise a local git repo inside the project folder
cd todo-app
git init

# 2. Stage all files for the first commit
git add .

# 3. Commit
git commit -m "initial commit: todo api with docker + fastapi + postgres"

# 4. Create a new repo on GitHub (github.com → New repository)
#    Name it todo-app, leave it empty (no README), then copy the remote URL.

# 5. Point your local repo at the remote
git remote add origin https://github.com/YOUR_USERNAME/todo-app.git

# 6. Rename the default branch to main (GitHub's standard)
git branch -M main

# 7. Push and set upstream tracking
git push -u origin main
```

> **What is a remote origin?**
> `origin` is just an alias for the full URL of your GitHub repo.
> The `-u` flag on the first push sets upstream tracking, so future `git push` (no arguments) knows where to send commits.

**After the first push, your normal workflow is just:**
```bash
git add .
git commit -m "describe what you changed"
git push
```

---

## 🔐 Secret Management — Do This Before Your First Commit

Hardcoded credentials in source code are one of the most common and costly security mistakes. This project uses `.env` files to keep secrets out of git entirely.

**How it works:**
- `.env.example` — a template with placeholder values, safe to commit, tells collaborators what variables are needed
- `.env` — your real secrets, listed in `.gitignore`, never committed, lives only on your machine and server

**Before your first commit, verify `.env` is ignored:**
```bash
cp .env.example .env
nano .env    # fill in a strong DB_PASSWORD

git status   # .env must NOT appear in this list — if it does, stop and check .gitignore
```

**If a secret ever ends up in a commit:**

The file being changed is not enough — the secret lives in git history even after you edit it. You need to rewrite history:

```bash
# Install git-filter-repo (the recommended tool for this)
pip install git-filter-repo

# Scrub the file containing the secret from all past commits
git filter-repo --path docker-compose.yml --invert-paths

# Re-add the clean version and commit
git add docker-compose.yml
git commit -m "fix: remove hardcoded secrets, use env vars"

# Force push the rewritten history
git push origin main --force
```

Then generate a new password and update your `.env` — treat any exposed secret as permanently compromised regardless of whether history was cleaned.

> The golden rule: secrets never go in code. `.env` files live only on the machine that runs the app, never in the repo.

---

## 🗂 Project Structure

```
todo-app/
├── app/
│   └── main.py            # FastAPI application (your backend)
├── .env.example           # Template — copy to .env, never commit .env
├── .gitignore             # Keeps .env and other junk out of git
├── Dockerfile             # Builds the API container image
├── docker-compose.yml     # Orchestrates api + db containers
└── requirements.txt       # Python dependencies
```

---

## 🐳 How Many Containers Do We Have?

**2 containers, 1 Dockerfile** — a common point of confusion.

| Container | Role | Defined by |
|---|---|---|
| `api` | Your FastAPI **backend** | Your `Dockerfile` — custom image |
| `db` | PostgreSQL **database** | `image: postgres:16-alpine` — pulled from Docker Hub |

You only write a Dockerfile when you need to *customise* an image. Postgres works out of the box — just pass it env vars. The `api` service is your backend code running in a container.

```
docker-compose.yml
 ├── api  →  build: .          (reads Dockerfile, builds your custom backend image)
 └── db   →  image: postgres   (pulls a ready-made image from Docker Hub)
```

Verify once running:
```bash
docker ps        # see both containers
docker images    # see your built api image + the postgres image
```

---

## 🚀 Running the App

```bash
# Copy secrets file and fill in your password
cp .env.example .env

# Build and start both containers
docker compose up --build

# Run in background
docker compose up --build -d

# Stop everything
docker compose down

# Stop AND delete the database volume (fresh start)
docker compose down -v
```

API: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

## ☁️ Deploying to AWS EC2

Running this on a cloud server frees up your local machine and is much closer to how real apps run in production.

**Step 1 — Launch the EC2 Instance**

Go to **console.aws.amazon.com → EC2 → Launch Instance** and fill in:

- **Name:** `todo-app`
- **AMI:** Ubuntu Server 24.04 LTS (Free Tier eligible)
- **Instance type:** `t2.micro` (free tier) or `t3.small` for more headroom
- **Key pair:** Click *Create new key pair* → name it `todo-app-key` → RSA → `.pem` → Download it. Keep it safe — you cannot re-download it.
- **Storage:** 20GB gp3 (bump from default 8GB — Docker images take space)

**Network settings → Edit → Create a new security group** called `todo-app-sg`:

| Type | Port | Source | Why |
|---|---|---|---|
| SSH | 22 | My IP | Only you can SSH in |
| HTTP | 80 | Anywhere | Frontend |
| Custom TCP | 8000 | Anywhere | API direct access (testing) |

Click **Launch Instance** and wait ~2 minutes for it to show **Running**.

---

**Step 2 — Connect to your instance**

Grab the **Public IPv4 address** from the instance details page, then:

```bash
# Fix key permissions (SSH refuses to connect without this)
chmod 400 ~/Downloads/todo-app-key.pem

# Connect (replace with your actual IP)
ssh -i ~/Downloads/todo-app-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

**Step 3 — Create a dedicated app user (recommended)**

The default `ubuntu` user has full `sudo` access — if your app is ever compromised, an attacker gets admin rights over the whole server. A dedicated user limits the blast radius.

```bash
# Create a dedicated user for running the app
sudo useradd -m -s /bin/bash appuser

# Add to docker group so they can run containers without sudo
sudo usermod -aG docker appuser

# Switch to the app user
sudo su - appuser
```

> **For a personal learning project** the `ubuntu` user is fine to keep things simple.
> In production or any shared server, always use a dedicated user.
> The pattern is: SSH in as `ubuntu` (admin) → `sudo su - appuser` to manage the app.

From here on, run all app commands as `appuser`.

---

**Step 4 — Install Docker on the server**
```bash
# Switch back to ubuntu to install Docker (needs sudo)
exit   # exits appuser back to ubuntu

# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker using the official convenience script
curl -fsSL https://get.docker.com | sudo sh

# Apply group change without logging out
newgrp docker

# Verify
docker --version
docker compose version

# Switch back to appuser to run the app
sudo su - appuser
```

---

**Step 5 — Clone your repo and configure secrets**
```bash
git clone https://github.com/YOUR_USERNAME/todo-app.git
cd todo-app

# Create .env with real values — this file never leaves the server
cp .env.example .env
nano .env
```

Your `.env` should look like:
```
DB_HOST=db
DB_PORT=5432
DB_NAME=todos
DB_USER=postgres
DB_PASSWORD=SomethingStrongHere123!
ALLOWED_ORIGINS=http://YOUR_EC2_PUBLIC_IP
```

Save with `Ctrl+O`, exit with `Ctrl+X`.

---

**Step 6 — Launch the app**
```bash
# Build images and start all 3 containers in the background
docker compose up --build -d

# Confirm all 3 containers are running
docker ps

# Watch logs to confirm no errors (Ctrl+C to exit)
docker compose logs -f
```

First run takes 2-3 minutes while Docker pulls base images and builds.

---

**Step 7 — Test it**

From your **local machine**:
```bash
# Health check
curl http://YOUR_EC2_PUBLIC_IP:8000/health

# API docs
open http://YOUR_EC2_PUBLIC_IP:8000/docs
```

Open **`http://YOUR_EC2_PUBLIC_IP`** in your browser — you should see the Todo UI.

---

**Updating the app after a code change:**
```bash
# On your local machine — commit and push
git add . && git commit -m "my change" && git push

# On the EC2 server — pull and rebuild
cd todo-app
git pull
docker compose up --build -d
```

> **Cost note:** A t2.micro runs free for 12 months under AWS Free Tier.
> Stop or terminate the instance when not in use to avoid unexpected charges.
> To stop: EC2 Console → select instance → Instance State → Stop.

---

## 🧪 Testing the API

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Docker", "description": "Containers are cool"}'

# List all todos
curl http://localhost:8000/todos

# Mark as completed
curl -X PATCH http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete a todo
curl -X DELETE http://localhost:8000/todos/1
```

---

## 🧠 What You're Learning

| Concept | Where it appears |
|---|---|
| **Dockerfile** | Building a custom image from `python:3.12-slim` |
| **Layers & caching** | Copying `requirements.txt` before source code |
| **Port mapping** | `"8000:8000"` in docker-compose |
| **Environment variables** | Secrets passed via `.env` → `environment:` |
| **Named volumes** | `postgres_data` persists DB between restarts |
| **Bind mounts** | `./app:/app/app` enables live code reload |
| **Health checks** | API waits for Postgres to be ready |
| **Service networking** | API connects to `db` via Docker's internal DNS |
| **Secret management** | `.env` file kept out of git via `.gitignore` |
| **Cloud deployment** | Running containers on a real Linux server (EC2) |

---

## 🔍 Useful Docker Commands

```bash
docker ps                          # running containers
docker compose logs -f api         # live API logs
docker compose exec api bash       # shell inside the API container
docker compose exec db psql -U postgres -d todos   # connect to DB
docker images                      # all images on your machine
docker system prune                # clean up unused resources
```

---

## ➡️ Next Steps

1. **Add Nginx** as a reverse proxy in front of the API (port 80 instead of 8000)
2. **Add HTTPS** with Certbot + Let's Encrypt (free SSL certificate)
3. **Multi-stage Dockerfile** — make the image smaller for production
4. **Add Redis** — cache the `/todos` list response
5. **Scale the API** — `docker compose up --scale api=3`
