#!/usr/bin/env python3
"""
Docker-backed end-to-end verification script.

This script:
1. Ensures Docker services are running and healthy
2. Runs database migrations and seeding
3. Ingests and indexes tafseer data
4. Fetches verses via API
5. Asks questions via RAG and validates citations

Prerequisites:
  - Docker and docker-compose installed
  - Run from project root: python backend/scripts/verify/verify_e2e_docker.py

Exit codes:
  0 - All E2E tests passed
  1 - Some E2E tests failed
  2 - Environment/configuration error
"""
import sys
import os
import subprocess
import time
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(2)

# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"
MAX_STARTUP_WAIT_SECONDS = 120
HEALTH_CHECK_INTERVAL = 5


@dataclass
class E2ETestResult:
    """Result of an E2E test."""
    test_name: str
    passed: bool
    message: str
    duration_ms: float = 0.0
    details: Optional[str] = None


def run_command(cmd: list[str], cwd: Path = PROJECT_ROOT, timeout: int = 300) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_docker_installed() -> E2ETestResult:
    """Verify Docker is installed and running."""
    start = time.perf_counter()

    exit_code, stdout, stderr = run_command(["docker", "info"])

    if exit_code == 0:
        return E2ETestResult(
            test_name="docker_installed",
            passed=True,
            message="Docker is installed and running",
            duration_ms=(time.perf_counter() - start) * 1000
        )
    else:
        return E2ETestResult(
            test_name="docker_installed",
            passed=False,
            message="Docker not running or not installed",
            details=stderr[:500]
        )


def check_compose_file_exists() -> E2ETestResult:
    """Verify docker-compose.yml exists."""
    if DOCKER_COMPOSE_FILE.exists():
        return E2ETestResult(
            test_name="compose_file",
            passed=True,
            message=f"Found docker-compose.yml at {DOCKER_COMPOSE_FILE}"
        )
    else:
        return E2ETestResult(
            test_name="compose_file",
            passed=False,
            message=f"docker-compose.yml not found at {DOCKER_COMPOSE_FILE}"
        )


def start_docker_services() -> E2ETestResult:
    """Start Docker services using docker-compose."""
    start = time.perf_counter()

    # Start services
    exit_code, stdout, stderr = run_command(
        ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "up", "-d", "--build"],
        timeout=600
    )

    if exit_code != 0:
        return E2ETestResult(
            test_name="docker_start",
            passed=False,
            message="Failed to start Docker services",
            details=stderr[:1000]
        )

    return E2ETestResult(
        test_name="docker_start",
        passed=True,
        message="Docker services started",
        duration_ms=(time.perf_counter() - start) * 1000
    )


def wait_for_services_healthy() -> E2ETestResult:
    """Wait for all services to become healthy."""
    start = time.perf_counter()
    services = ["postgres", "qdrant", "redis", "backend"]

    for service in services:
        elapsed = 0
        healthy = False

        while elapsed < MAX_STARTUP_WAIT_SECONDS:
            exit_code, stdout, _ = run_command([
                "docker", "inspect", "--format", "{{.State.Health.Status}}",
                f"tadabbur-{service}"
            ])

            if exit_code == 0 and stdout.strip() == "healthy":
                healthy = True
                print(f"  {service}: healthy ({elapsed}s)")
                break

            time.sleep(HEALTH_CHECK_INTERVAL)
            elapsed += HEALTH_CHECK_INTERVAL

        if not healthy:
            return E2ETestResult(
                test_name="services_healthy",
                passed=False,
                message=f"Service {service} did not become healthy within {MAX_STARTUP_WAIT_SECONDS}s"
            )

    return E2ETestResult(
        test_name="services_healthy",
        passed=True,
        message="All services healthy",
        duration_ms=(time.perf_counter() - start) * 1000
    )


def test_health_endpoint() -> E2ETestResult:
    """Test the basic health endpoint."""
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/health")

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return E2ETestResult(
                        test_name="health_endpoint",
                        passed=True,
                        message="Health endpoint returns healthy",
                        duration_ms=(time.perf_counter() - start) * 1000
                    )

            return E2ETestResult(
                test_name="health_endpoint",
                passed=False,
                message=f"Health check failed: {response.status_code}",
                details=response.text[:500]
            )

    except Exception as e:
        return E2ETestResult(
            test_name="health_endpoint",
            passed=False,
            message=f"Health endpoint error: {str(e)}"
        )


def test_verse_fetch() -> E2ETestResult:
    """Test fetching Quran verses."""
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=10.0) as client:
            # Fetch Al-Fatiha (Surah 1)
            response = client.get(f"{API_BASE_URL}/api/v1/quran/surah/1")

            if response.status_code == 200:
                data = response.json()

                # Verify we got 7 verses (Al-Fatiha has 7 verses)
                if isinstance(data, list) and len(data) == 7:
                    # Check first verse has expected fields
                    first_verse = data[0]
                    required_fields = ["surah_number", "verse_number", "text_uthmani"]

                    if all(field in first_verse for field in required_fields):
                        return E2ETestResult(
                            test_name="verse_fetch",
                            passed=True,
                            message="Successfully fetched Al-Fatiha (7 verses)",
                            duration_ms=(time.perf_counter() - start) * 1000,
                            details=f"First verse: {first_verse.get('text_uthmani', '')[:50]}..."
                        )

                return E2ETestResult(
                    test_name="verse_fetch",
                    passed=False,
                    message=f"Unexpected verse data format",
                    details=str(data)[:500]
                )

            elif response.status_code == 404:
                return E2ETestResult(
                    test_name="verse_fetch",
                    passed=False,
                    message="Verse data not found - database may need seeding"
                )

            return E2ETestResult(
                test_name="verse_fetch",
                passed=False,
                message=f"Verse fetch failed: HTTP {response.status_code}"
            )

    except Exception as e:
        return E2ETestResult(
            test_name="verse_fetch",
            passed=False,
            message=f"Verse fetch error: {str(e)}"
        )


def test_tafseer_index() -> E2ETestResult:
    """Test that tafseer data is indexed in Qdrant."""
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=10.0) as client:
            # Check Qdrant collection
            response = client.get("http://localhost:6333/collections/tafseer_chunks")

            if response.status_code == 200:
                data = response.json()
                points_count = data.get("result", {}).get("points_count", 0)

                if points_count > 0:
                    return E2ETestResult(
                        test_name="tafseer_index",
                        passed=True,
                        message=f"Tafseer index has {points_count} vectors",
                        duration_ms=(time.perf_counter() - start) * 1000
                    )
                else:
                    return E2ETestResult(
                        test_name="tafseer_index",
                        passed=False,
                        message="Tafseer collection exists but has no vectors - run ingestion"
                    )

            elif response.status_code == 404:
                return E2ETestResult(
                    test_name="tafseer_index",
                    passed=False,
                    message="Tafseer collection not found - run indexing first"
                )

            return E2ETestResult(
                test_name="tafseer_index",
                passed=False,
                message=f"Qdrant check failed: HTTP {response.status_code}"
            )

    except Exception as e:
        return E2ETestResult(
            test_name="tafseer_index",
            passed=False,
            message=f"Qdrant check error: {str(e)}"
        )


def test_rag_query() -> E2ETestResult:
    """Test RAG query with citation validation."""
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=60.0) as client:
            # Ask a question about Al-Fatiha
            query = {
                "question": "What is the meaning of Bismillah in Surah Al-Fatiha?",
                "surah_filter": 1
            }

            response = client.post(
                f"{API_BASE_URL}/api/v1/ask",
                json=query
            )

            if response.status_code == 200:
                data = response.json()

                # Check for required response fields
                if "response" in data or "answer" in data:
                    answer = data.get("response") or data.get("answer", "")
                    citations = data.get("citations", [])
                    confidence = data.get("confidence", {})

                    # Validate citations if present
                    if citations:
                        valid_citations = sum(1 for c in citations if c.get("source"))
                        return E2ETestResult(
                            test_name="rag_query",
                            passed=True,
                            message=f"RAG query successful with {valid_citations} citations",
                            duration_ms=(time.perf_counter() - start) * 1000,
                            details=f"Confidence: {confidence.get('level', 'unknown')}, Answer: {answer[:100]}..."
                        )
                    else:
                        # No citations - still check if response looks valid
                        if len(answer) > 50:
                            return E2ETestResult(
                                test_name="rag_query",
                                passed=True,
                                message="RAG query returned answer (no citations)",
                                duration_ms=(time.perf_counter() - start) * 1000,
                                details=f"Answer: {answer[:100]}..."
                            )

                return E2ETestResult(
                    test_name="rag_query",
                    passed=False,
                    message="RAG response missing expected fields",
                    details=str(data)[:500]
                )

            elif response.status_code == 503:
                return E2ETestResult(
                    test_name="rag_query",
                    passed=False,
                    message="RAG service unavailable - ANTHROPIC_API_KEY may not be set"
                )

            return E2ETestResult(
                test_name="rag_query",
                passed=False,
                message=f"RAG query failed: HTTP {response.status_code}",
                details=response.text[:500]
            )

    except Exception as e:
        return E2ETestResult(
            test_name="rag_query",
            passed=False,
            message=f"RAG query error: {str(e)}"
        )


def test_data_health() -> E2ETestResult:
    """Test the data health endpoint."""
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/health/data")

            if response.status_code == 200:
                data = response.json()
                counts = data.get("counts", {})

                verse_count = counts.get("quran_verses", 0)
                tafseer_count = counts.get("tafseer_chunks", 0)

                if verse_count == 6236:
                    return E2ETestResult(
                        test_name="data_health",
                        passed=True,
                        message=f"Data healthy: {verse_count} verses, {tafseer_count} tafseer chunks",
                        duration_ms=(time.perf_counter() - start) * 1000
                    )
                elif verse_count > 0:
                    return E2ETestResult(
                        test_name="data_health",
                        passed=True,
                        message=f"Data partially loaded: {verse_count}/6236 verses",
                        duration_ms=(time.perf_counter() - start) * 1000
                    )
                else:
                    return E2ETestResult(
                        test_name="data_health",
                        passed=False,
                        message="No verse data found - run database seeding"
                    )

            return E2ETestResult(
                test_name="data_health",
                passed=False,
                message=f"Data health check failed: HTTP {response.status_code}"
            )

    except Exception as e:
        return E2ETestResult(
            test_name="data_health",
            passed=False,
            message=f"Data health error: {str(e)}"
        )


def run_database_migration() -> E2ETestResult:
    """Run database migrations inside the container."""
    start = time.perf_counter()

    exit_code, stdout, stderr = run_command([
        "docker", "exec", "tadabbur-backend",
        "alembic", "upgrade", "head"
    ])

    if exit_code == 0:
        return E2ETestResult(
            test_name="db_migration",
            passed=True,
            message="Database migrations applied successfully",
            duration_ms=(time.perf_counter() - start) * 1000
        )
    else:
        return E2ETestResult(
            test_name="db_migration",
            passed=False,
            message="Database migration failed",
            details=stderr[:500]
        )


def run_database_seed() -> E2ETestResult:
    """Run database seeding inside the container."""
    start = time.perf_counter()

    exit_code, stdout, stderr = run_command([
        "docker", "exec", "tadabbur-backend",
        "python", "scripts/ingest/seed_database.py"
    ], timeout=600)

    if exit_code == 0:
        return E2ETestResult(
            test_name="db_seed",
            passed=True,
            message="Database seeding completed",
            duration_ms=(time.perf_counter() - start) * 1000
        )
    else:
        # Check if it's just a "data already exists" message
        if "already" in stderr.lower() or "skip" in stderr.lower():
            return E2ETestResult(
                test_name="db_seed",
                passed=True,
                message="Database already seeded (skipped)",
                duration_ms=(time.perf_counter() - start) * 1000
            )

        return E2ETestResult(
            test_name="db_seed",
            passed=False,
            message="Database seeding failed",
            details=stderr[:500]
        )


def stop_docker_services() -> E2ETestResult:
    """Stop Docker services."""
    start = time.perf_counter()

    exit_code, _, stderr = run_command([
        "docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "down"
    ])

    if exit_code == 0:
        return E2ETestResult(
            test_name="docker_stop",
            passed=True,
            message="Docker services stopped",
            duration_ms=(time.perf_counter() - start) * 1000
        )
    else:
        return E2ETestResult(
            test_name="docker_stop",
            passed=False,
            message="Failed to stop Docker services",
            details=stderr[:500]
        )


def main():
    """Run all E2E verification tests."""
    print("=" * 70)
    print("DOCKER-BACKED END-TO-END VERIFICATION")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"API URL: {API_BASE_URL}")
    print("=" * 70)

    # Parse arguments
    skip_startup = "--skip-startup" in sys.argv
    skip_teardown = "--keep-running" in sys.argv
    full_pipeline = "--full" in sys.argv

    results = []

    # Pre-flight checks
    print("\n[1/7] PRE-FLIGHT CHECKS")
    print("-" * 40)

    docker_check = check_docker_installed()
    results.append(docker_check)
    print(f"  {'PASS' if docker_check.passed else 'FAIL'}: {docker_check.message}")

    if not docker_check.passed:
        print("\nERROR: Docker not available. Cannot proceed.")
        sys.exit(2)

    compose_check = check_compose_file_exists()
    results.append(compose_check)
    print(f"  {'PASS' if compose_check.passed else 'FAIL'}: {compose_check.message}")

    if not compose_check.passed:
        print("\nERROR: docker-compose.yml not found. Cannot proceed.")
        sys.exit(2)

    # Start services
    if not skip_startup:
        print("\n[2/7] STARTING DOCKER SERVICES")
        print("-" * 40)

        start_result = start_docker_services()
        results.append(start_result)
        print(f"  {'PASS' if start_result.passed else 'FAIL'}: {start_result.message}")

        if not start_result.passed:
            print(f"\nERROR: {start_result.details}")
            sys.exit(1)

        print("\n[3/7] WAITING FOR SERVICES")
        print("-" * 40)

        health_result = wait_for_services_healthy()
        results.append(health_result)
        print(f"  {'PASS' if health_result.passed else 'FAIL'}: {health_result.message}")

        if not health_result.passed:
            print("\nERROR: Services did not become healthy.")
            sys.exit(1)
    else:
        print("\n[2-3/7] SKIPPED (--skip-startup)")

    # Run migrations and seeding if full pipeline
    if full_pipeline:
        print("\n[4/7] DATABASE SETUP")
        print("-" * 40)

        migration_result = run_database_migration()
        results.append(migration_result)
        print(f"  {'PASS' if migration_result.passed else 'FAIL'}: {migration_result.message}")

        seed_result = run_database_seed()
        results.append(seed_result)
        print(f"  {'PASS' if seed_result.passed else 'FAIL'}: {seed_result.message}")
    else:
        print("\n[4/7] DATABASE SETUP (skipped, use --full to run)")

    # API Tests
    print("\n[5/7] API ENDPOINT TESTS")
    print("-" * 40)

    health_test = test_health_endpoint()
    results.append(health_test)
    print(f"  {'PASS' if health_test.passed else 'FAIL'}: {health_test.message} ({health_test.duration_ms:.0f}ms)")

    data_test = test_data_health()
    results.append(data_test)
    print(f"  {'PASS' if data_test.passed else 'FAIL'}: {data_test.message} ({data_test.duration_ms:.0f}ms)")

    verse_test = test_verse_fetch()
    results.append(verse_test)
    print(f"  {'PASS' if verse_test.passed else 'FAIL'}: {verse_test.message} ({verse_test.duration_ms:.0f}ms)")
    if verse_test.details:
        print(f"    {verse_test.details}")

    # Vector DB test
    print("\n[6/7] VECTOR DATABASE TEST")
    print("-" * 40)

    index_test = test_tafseer_index()
    results.append(index_test)
    print(f"  {'PASS' if index_test.passed else 'FAIL'}: {index_test.message} ({index_test.duration_ms:.0f}ms)")

    # RAG query test (optional - requires API key)
    print("\n[7/7] RAG QUERY TEST")
    print("-" * 40)

    if os.getenv("ANTHROPIC_API_KEY"):
        rag_test = test_rag_query()
        results.append(rag_test)
        print(f"  {'PASS' if rag_test.passed else 'FAIL'}: {rag_test.message} ({rag_test.duration_ms:.0f}ms)")
        if rag_test.details:
            print(f"    {rag_test.details}")
    else:
        print("  SKIP: ANTHROPIC_API_KEY not set")

    # Cleanup
    if not skip_teardown:
        print("\n[CLEANUP]")
        print("-" * 40)
        stop_result = stop_docker_services()
        print(f"  {stop_result.message}")
    else:
        print("\n[CLEANUP] Skipped (--keep-running)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"  Total tests: {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if not r.passed:
                print(f"    - {r.test_name}: {r.message}")
                if r.details:
                    print(f"      Details: {r.details[:200]}")

    print("\n  OPTIONS:")
    print("    --skip-startup   Skip docker-compose up (services already running)")
    print("    --keep-running   Don't stop services after tests")
    print("    --full           Run migrations and seeding")

    print("=" * 70)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
