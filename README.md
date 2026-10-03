# GradApp Docker Setup

The Compose configuration starts three containers:

- React frontend on `http://localhost:3000`
- Django API on `http://localhost:8000`
- PostgreSQL database on the private Docker network

## Start the complete project

From the project root containing `frontend`, `backend`, and `docker-compose.yml`:

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000` in a browser. The backend automatically applies database migrations and inserts sample programs.

## Stop the project

```bash
docker compose down
```

## Stop and remove the development database

```bash
docker compose down --volumes
```

The last command permanently removes the Docker database volume and should only be used when a clean database is required.
