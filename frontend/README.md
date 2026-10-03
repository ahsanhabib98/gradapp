# GradApp Frontend

A simple responsive React interface for the GradApp graduate-program discovery platform.

## Included screens

- Account registration and login
- Program discovery dashboard
- Search and filters
- Program details
- Student profile form
- Responsive desktop, tablet, and mobile layout

## Run locally

```bash
cp .env.example .env
npm install
npm run dev
```

The app opens at `http://localhost:5173` and expects the Django API at `http://localhost:8000/api`.

## Build

```bash
npm run build
```

## Docker

```bash
docker build -t gradapp-frontend .
docker run --rm -p 3000:80 gradapp-frontend
```

Then open `http://localhost:3000`.
