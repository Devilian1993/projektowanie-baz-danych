import subprocess
import time
from pathlib import Path

SOURCE_CONTAINER = "proj-db-postgres"
TARGET_CONTAINER = "proj-db-postgres-indexed"
IMAGE = "postgres:16-alpine"
INDEX_SQL_PATH = Path("../sql/indexes/add_indexes.sql")


def load_env(env_path: str = "../.env") -> dict[str, str]:
    env = {}
    for line in Path(env_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def wait_for_postgres(container: str, user: str, dbname: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        res = subprocess.run(
            ["docker", "exec", container, "pg_isready", "-h", "127.0.0.1", "-U", user, "-d", dbname],
            capture_output=True,
        )
        if res.returncode == 0:
            return
        time.sleep(1)
    raise TimeoutError(f"Container {container} did not start within {timeout}s.")


def main() -> None:
    if not INDEX_SQL_PATH.exists():
        raise FileNotFoundError(f"File not found: {INDEX_SQL_PATH}")

    env = load_env()
    user = env["POSTGRES_USER"]
    password = env["POSTGRES_PASSWORD"]
    dbname = env["POSTGRES_DB"]
    target_port = int(env.get("POSTGRES_PORT", "5432")) + 1

    subprocess.run(["docker", "rm", "-f", "-v", TARGET_CONTAINER], capture_output=True)

    print(f"Starting container '{TARGET_CONTAINER}' on port {target_port}...")
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", TARGET_CONTAINER,
            "-e", f"POSTGRES_DB={dbname}",
            "-e", f"POSTGRES_USER={user}",
            "-e", f"POSTGRES_PASSWORD={password}",
            "-p", f"{target_port}:5432",
            IMAGE,
        ],
        check=True,
    )

    wait_for_postgres(TARGET_CONTAINER, user, dbname)

    print(f"Copying data from '{SOURCE_CONTAINER}' to '{TARGET_CONTAINER}'...")
    dump = subprocess.run(
        ["docker", "exec", SOURCE_CONTAINER, "pg_dump", "-U", user, "-d", dbname],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["docker", "exec", "-i", TARGET_CONTAINER, "psql", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", dbname],
        input=dump.stdout,
        check=True,
    )

    print(f"Executing {INDEX_SQL_PATH} on '{TARGET_CONTAINER}'...")
    subprocess.run(
        ["docker", "exec", "-i", TARGET_CONTAINER, "psql", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", dbname],
        input=INDEX_SQL_PATH.read_bytes(),
        check=True,
    )

    print("Done:")
    print(f"  - Database without indexes: localhost:{env.get('POSTGRES_PORT', '5432')} ({SOURCE_CONTAINER})")
    print(f"  - Database with indexes:    localhost:{target_port} ({TARGET_CONTAINER})")


if __name__ == "__main__":
    main()