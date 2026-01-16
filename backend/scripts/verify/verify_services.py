#!/usr/bin/env python3
"""
Verify all required services are reachable.

Provides comprehensive diagnostics on failure:
- Docker daemon status
- Container health status
- Port availability
- Compose file presence
- Troubleshooting hints

Exit codes:
  0 - All services healthy
  1 - One or more services unhealthy
  2 - Environment/configuration error
"""
import sys
import os
import subprocess
import socket
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(2)

try:
    import redis
except ImportError:
    print("ERROR: redis not installed. Run: pip install redis")
    sys.exit(2)

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(2)


# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
REQUIRED_PORTS = {
    5432: "PostgreSQL",
    6333: "Qdrant",
    6379: "Redis",
}
CONTAINER_NAMES = {
    "postgres": "tadabbur-postgres",
    "qdrant": "tadabbur-qdrant",
    "redis": "tadabbur-redis",
}


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    name: str
    passed: bool
    message: str
    hint: Optional[str] = None


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def check_docker_daemon() -> DiagnosticResult:
    """Check if Docker daemon is running."""
    exit_code, stdout, stderr = run_command(["docker", "info"])

    if exit_code == 0:
        return DiagnosticResult(
            name="Docker Daemon",
            passed=True,
            message="Docker daemon is running"
        )
    else:
        return DiagnosticResult(
            name="Docker Daemon",
            passed=False,
            message="Docker daemon not running",
            hint="Start with: sudo systemctl start docker"
        )


def check_compose_file() -> DiagnosticResult:
    """Check if docker-compose.yml exists."""
    if COMPOSE_FILE.exists():
        return DiagnosticResult(
            name="Compose File",
            passed=True,
            message=f"Found: {COMPOSE_FILE}"
        )
    else:
        return DiagnosticResult(
            name="Compose File",
            passed=False,
            message=f"Not found: {COMPOSE_FILE}",
            hint="Ensure you're in the project root directory"
        )


def check_port_available(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def check_ports() -> list[DiagnosticResult]:
    """Check if required ports are available/in-use."""
    results = []
    for port, service in REQUIRED_PORTS.items():
        in_use = check_port_available(port)
        if in_use:
            results.append(DiagnosticResult(
                name=f"Port {port} ({service})",
                passed=True,
                message=f"Port {port} is responding"
            ))
        else:
            results.append(DiagnosticResult(
                name=f"Port {port} ({service})",
                passed=False,
                message=f"Port {port} is not responding",
                hint=f"Check if {service} container is running"
            ))
    return results


def get_container_status() -> dict:
    """Get status of Docker containers."""
    statuses = {}
    for service, container in CONTAINER_NAMES.items():
        exit_code, stdout, stderr = run_command([
            "docker", "inspect", "--format",
            "{{.State.Status}}|{{.State.Health.Status}}",
            container
        ])
        if exit_code == 0:
            parts = stdout.strip().split("|")
            statuses[service] = {
                "status": parts[0] if parts else "unknown",
                "health": parts[1] if len(parts) > 1 else "unknown"
            }
        else:
            statuses[service] = {"status": "not_found", "health": "unknown"}
    return statuses


def get_docker_compose_cmd() -> list[str]:
    """Detect which docker compose command is available."""
    # Try docker compose (V2) first
    exit_code, _, _ = run_command(["docker", "compose", "version"])
    if exit_code == 0:
        return ["docker", "compose"]
    # Fall back to docker-compose (V1)
    return ["docker-compose"]


def get_compose_ps_output() -> str:
    """Get docker compose ps output."""
    compose_cmd = get_docker_compose_cmd()
    exit_code, stdout, stderr = run_command(
        compose_cmd + ["-f", str(COMPOSE_FILE), "ps"]
    )
    if exit_code == 0:
        return stdout
    return f"Error: {stderr}"


def check_postgres(host: str, port: int, user: str, password: str, db: str) -> DiagnosticResult:
    """Check PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=db,
            connect_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return DiagnosticResult(
            name="PostgreSQL",
            passed=True,
            message=f"Connected successfully",
        )
    except psycopg2.OperationalError as e:
        error_msg = str(e).split('\n')[0]
        return DiagnosticResult(
            name="PostgreSQL",
            passed=False,
            message=f"Connection failed: {error_msg}",
            hint="Check: docker compose logs postgres"
        )
    except Exception as e:
        return DiagnosticResult(
            name="PostgreSQL",
            passed=False,
            message=f"Error: {str(e)}"
        )


def check_qdrant(host: str, port: int) -> DiagnosticResult:
    """Check Qdrant connection."""
    try:
        # Qdrant uses /healthz endpoint (not /readiness)
        response = httpx.get(
            f"http://{host}:{port}/healthz",
            timeout=5.0,
        )
        if response.status_code == 200:
            return DiagnosticResult(
                name="Qdrant",
                passed=True,
                message="Connected successfully"
            )
        return DiagnosticResult(
            name="Qdrant",
            passed=False,
            message=f"Returned status {response.status_code}",
            hint="Check: docker compose logs qdrant"
        )
    except httpx.ConnectError:
        return DiagnosticResult(
            name="Qdrant",
            passed=False,
            message="Connection refused",
            hint="Check: docker compose logs qdrant"
        )
    except Exception as e:
        return DiagnosticResult(
            name="Qdrant",
            passed=False,
            message=f"Error: {str(e)}"
        )


def check_redis(url: str) -> DiagnosticResult:
    """Check Redis connection."""
    try:
        r = redis.from_url(url, socket_connect_timeout=5)
        r.ping()
        info = r.info("server")
        r.close()
        return DiagnosticResult(
            name="Redis",
            passed=True,
            message=f"Connected successfully (v{info.get('redis_version', 'unknown')})"
        )
    except redis.ConnectionError as e:
        return DiagnosticResult(
            name="Redis",
            passed=False,
            message="Connection refused",
            hint="Check: docker compose logs redis"
        )
    except Exception as e:
        return DiagnosticResult(
            name="Redis",
            passed=False,
            message=f"Error: {str(e)}"
        )


def main():
    """Run all service checks with comprehensive diagnostics."""
    print("=" * 70)
    print("SERVICE VERIFICATION")
    print("=" * 70)

    all_diagnostics = []
    all_passed = True

    # Pre-flight checks
    print("\n--- PRE-FLIGHT CHECKS ---")

    docker_check = check_docker_daemon()
    all_diagnostics.append(docker_check)
    status = "PASS" if docker_check.passed else "FAIL"
    print(f"  [{status}] {docker_check.name}: {docker_check.message}")
    if not docker_check.passed:
        if docker_check.hint:
            print(f"        Hint: {docker_check.hint}")
        print("\n" + "=" * 70)
        print("OVERALL: FAIL - Docker daemon not running")
        print("=" * 70)
        print("\nDocker must be running before services can be verified.")
        print("Start Docker with: sudo systemctl start docker")
        sys.exit(1)

    compose_check = check_compose_file()
    all_diagnostics.append(compose_check)
    status = "PASS" if compose_check.passed else "FAIL"
    print(f"  [{status}] {compose_check.name}: {compose_check.message}")
    if not compose_check.passed:
        all_passed = False

    # Container status
    print("\n--- CONTAINER STATUS ---")
    container_statuses = get_container_status()
    for service, info in container_statuses.items():
        status_str = info["status"]
        health_str = info["health"]
        if status_str == "running" and health_str == "healthy":
            print(f"  [PASS] {service}: running (healthy)")
        elif status_str == "running":
            print(f"  [WARN] {service}: running ({health_str})")
        elif status_str == "not_found":
            print(f"  [FAIL] {service}: container not found")
            all_passed = False
        else:
            print(f"  [FAIL] {service}: {status_str}")
            all_passed = False

    # Load configuration from environment
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    pg_user = os.getenv("POSTGRES_USER", "tadabbur")
    pg_pass = os.getenv("POSTGRES_PASSWORD", "tadabbur_dev")
    pg_db = os.getenv("POSTGRES_DB", "tadabbur")

    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Service connectivity checks
    print("\n--- SERVICE CONNECTIVITY ---")

    # Check PostgreSQL
    print("\n[1/3] Checking PostgreSQL...")
    pg_result = check_postgres(pg_host, pg_port, pg_user, pg_pass, pg_db)
    all_diagnostics.append(pg_result)
    status = "PASS" if pg_result.passed else "FAIL"
    print(f"  [{status}] {pg_result.message}")
    if not pg_result.passed:
        all_passed = False
        if pg_result.hint:
            print(f"        Hint: {pg_result.hint}")

    # Check Qdrant
    print("\n[2/3] Checking Qdrant...")
    qdrant_result = check_qdrant(qdrant_host, qdrant_port)
    all_diagnostics.append(qdrant_result)
    status = "PASS" if qdrant_result.passed else "FAIL"
    print(f"  [{status}] {qdrant_result.message}")
    if not qdrant_result.passed:
        all_passed = False
        if qdrant_result.hint:
            print(f"        Hint: {qdrant_result.hint}")

    # Check Redis
    print("\n[3/3] Checking Redis...")
    redis_result = check_redis(redis_url)
    all_diagnostics.append(redis_result)
    status = "PASS" if redis_result.passed else "FAIL"
    print(f"  [{status}] {redis_result.message}")
    if not redis_result.passed:
        all_passed = False
        if redis_result.hint:
            print(f"        Hint: {redis_result.hint}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    service_results = [pg_result, qdrant_result, redis_result]
    for result in service_results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  {result.name}: {status}")

    print("\n" + "=" * 70)

    if all_passed:
        print("OVERALL: PASS - All services healthy")
        print("=" * 70)
        sys.exit(0)
    else:
        print("OVERALL: FAIL - One or more services unhealthy")
        print("=" * 70)

        # Show docker compose ps output
        print("\n--- DOCKER COMPOSE STATUS ---")
        print(get_compose_ps_output())

        print("\n--- TROUBLESHOOTING ---")
        print("")
        print("  COMMON CAUSES:")
        print("    1. Services not started: make up")
        print("    2. Container crashed: make logs-service SERVICE=<service>")
        print("    3. Port conflict: make check-ports")
        print("    4. Docker not running: sudo systemctl start docker")
        print("")
        print("  QUICK FIX:")
        print("    make ensure-services   # Auto-start and wait for health")
        print("")
        print("  VIEW LOGS:")
        print("    make logs-service SERVICE=postgres")
        print("    make logs-service SERVICE=qdrant")
        print("    make logs-service SERVICE=redis")
        print("")
        sys.exit(1)


if __name__ == "__main__":
    main()
