# Docker Installation Required

## Issue
Docker Desktop is not installed on this system. Required for PostgreSQL and Redis.

## Installation Steps

### Option 1: Docker Desktop (Recommended)
1. Download Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Once installed, run: `docker compose up -d` from project root

### Option 2: Manual PostgreSQL + Redis (Alternative)
If you prefer not to install Docker, you can install PostgreSQL and Redis natively:

**PostgreSQL 15:**
- Download: https://www.postgresql.org/download/windows/
- During install, create database: `eduplat`
- Create user: `eduuser` with password: `edupass123`
- Grant privileges to user

**Redis 7:**
- Download: https://github.com/microsoftarchive/redis/releases (or use Memurai)
- Install and run on default port 6379

**Update `.env` if using different credentials.**

## Next Steps
1. Install Docker Desktop OR install PostgreSQL + Redis manually
2. Add GEMINI_API_KEY to `backend/.env` (see ENV_CONFIG.md)
3. Run verification test

## Current Status
- Git initialized ✅
- Docker compose file ready ✅
- Documentation complete ✅
- Waiting for: Docker installation + API key
