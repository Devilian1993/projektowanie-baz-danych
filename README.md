# Requirements
* Docker
* Docker Compose

# Structure
```text
.
├── docker-compose.yml       # PostgreSQL and volumes configuration
├── .env.example             # Example of env variables
├── .env                     # Local env variables (in .gitignore)
└── sql/                     # Start scripts (executed in lexicographical order)
    └── 01_schema.sql        # Table definitions
```

# Deployment

1. Prepare `.env` by copying `.env.example` and change values to your needs:
```bash
cp .env.example .env
```
*(Make sure your `.env` contains: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_PORT`)*

2. Start the database (`-d` flag starts it in the background):
```bash
docker compose up -d
```

3. Verify that the container has started and is working properly:
```bash
docker compose ps
```

or check the initialization logs:
```bash
docker compose logs -f db
```

# Entering the container (psql)

Replace `your_user` and `your_database_name` with the exact values you set in your `.env` file (e.g., `POSTGRES_DB=silownia`):
```bash
docker compose exec db psql -U your_user -d your_database_name
```

# Stopping the container

Stops the container without removing it (data is preserved):
```bash
docker compose stop
```

# Restarting the container

Starts a previously stopped container:
```bash
docker compose start
```

# Shutting down the container

Stops and removes the container and network (data in the volume is preserved):
```bash
docker compose down
```

# Full database reset

**WARNING:** This will delete all data inside the database (removes the volume) and force the initialization scripts to run again.
```bash
docker compose down -v
docker compose up -d
```
