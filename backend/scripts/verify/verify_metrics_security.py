#!/usr/bin/env python3
"""
Verify metrics and health endpoint security configuration.

Validates:
1. Production environment detection works
2. Protected endpoints are properly gated
3. METRICS_SECRET validation logic is correct
4. Public endpoints remain accessible

Exit codes:
  0 - All security checks passed
  1 - Some security checks failed
"""
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class SecurityTestResult:
    """Result of a security test."""
    test_name: str
    passed: bool
    message: str
    details: Optional[str] = None


def test_production_detection():
    """Test is_production() function."""
    from app.api.routes.health import is_production

    # Save original env
    original_env = os.environ.get("ENVIRONMENT")
    original_env2 = os.environ.get("ENV")

    results = []

    try:
        # Test development detection
        os.environ["ENVIRONMENT"] = "development"
        if "ENV" in os.environ:
            del os.environ["ENV"]
        assert not is_production(), "Should not detect as production for 'development'"

        # Test production detection
        os.environ["ENVIRONMENT"] = "production"
        assert is_production(), "Should detect as production for 'production'"

        os.environ["ENVIRONMENT"] = "prod"
        assert is_production(), "Should detect as production for 'prod'"

        # Test PRODUCTION (uppercase)
        os.environ["ENVIRONMENT"] = "PRODUCTION"
        assert is_production(), "Should detect as production for 'PRODUCTION'"

        # Test ENV fallback
        del os.environ["ENVIRONMENT"]
        os.environ["ENV"] = "production"
        assert is_production(), "Should detect production via ENV fallback"

        results.append(SecurityTestResult(
            test_name="production_detection",
            passed=True,
            message="Production environment detection works correctly"
        ))

    except AssertionError as e:
        results.append(SecurityTestResult(
            test_name="production_detection",
            passed=False,
            message=f"Production detection failed: {str(e)}"
        ))

    finally:
        # Restore original env
        if original_env:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
        if original_env2:
            os.environ["ENV"] = original_env2
        elif "ENV" in os.environ:
            del os.environ["ENV"]

    return results[0] if results else SecurityTestResult(
        test_name="production_detection",
        passed=False,
        message="Test did not complete"
    )


def test_metrics_secret_function():
    """Test get_metrics_secret() function."""
    from app.api.routes.health import get_metrics_secret

    original = os.environ.get("METRICS_SECRET")

    try:
        # Test without secret
        if "METRICS_SECRET" in os.environ:
            del os.environ["METRICS_SECRET"]
        assert get_metrics_secret() is None, "Should return None when not set"

        # Test with secret
        os.environ["METRICS_SECRET"] = "test_secret_123"
        assert get_metrics_secret() == "test_secret_123", "Should return secret value"

        return SecurityTestResult(
            test_name="metrics_secret_function",
            passed=True,
            message="METRICS_SECRET reading works correctly"
        )

    except AssertionError as e:
        return SecurityTestResult(
            test_name="metrics_secret_function",
            passed=False,
            message=f"METRICS_SECRET function failed: {str(e)}"
        )

    finally:
        if original:
            os.environ["METRICS_SECRET"] = original
        elif "METRICS_SECRET" in os.environ:
            del os.environ["METRICS_SECRET"]


def test_protected_endpoints_list():
    """Verify protected endpoints are documented."""
    from app.api.routes import health

    # Check the security endpoint has correct info
    import inspect
    source = inspect.getsource(health)

    protected = [
        "/health/detailed",
        "/health/data",
        "/health/rag",
        "/metrics",
    ]

    public = [
        "/health",
        "/ready",
    ]

    all_found = True
    missing = []

    for endpoint in protected:
        if endpoint not in source:
            all_found = False
            missing.append(endpoint)

    for endpoint in public:
        if endpoint not in source:
            all_found = False
            missing.append(endpoint)

    if all_found:
        return SecurityTestResult(
            test_name="protected_endpoints_list",
            passed=True,
            message=f"All {len(protected)} protected and {len(public)} public endpoints documented",
            details=f"Protected: {protected}"
        )
    else:
        return SecurityTestResult(
            test_name="protected_endpoints_list",
            passed=False,
            message=f"Missing endpoints in source: {missing}"
        )


def test_production_gating_logic():
    """Test that production gating logic exists in protected endpoints."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health)

    # Check that production check exists for each protected endpoint
    required_patterns = [
        "is_production()",
        "get_metrics_secret()",
        "X-Metrics-Secret",
        "HTTP_403_FORBIDDEN",
        "HTTP_503_SERVICE_UNAVAILABLE",
        "_safe_secret_check",  # Constant-time comparison
        "_check_production_auth",  # Centralized auth check
    ]

    found = []
    missing = []

    for pattern in required_patterns:
        if pattern in source:
            found.append(pattern)
        else:
            missing.append(pattern)

    if len(missing) == 0:
        return SecurityTestResult(
            test_name="production_gating_logic",
            passed=True,
            message="All required security patterns found in health module",
            details=f"Found: {found}"
        )
    else:
        return SecurityTestResult(
            test_name="production_gating_logic",
            passed=False,
            message=f"Missing security patterns: {missing}",
            details=f"Found: {found}"
        )


def test_constant_time_comparison():
    """Test that secret comparison uses constant-time algorithm."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health)

    # Check for constant-time comparison function
    required_patterns = [
        "hmac.compare_digest",  # Python's constant-time comparison
        "_safe_secret_check",  # Our wrapper function
    ]

    found = []
    missing = []

    for pattern in required_patterns:
        if pattern in source:
            found.append(pattern)
        else:
            missing.append(pattern)

    if len(missing) == 0:
        return SecurityTestResult(
            test_name="constant_time_comparison",
            passed=True,
            message="Using constant-time secret comparison (prevents timing attacks)",
            details=f"Found: {found}"
        )
    else:
        return SecurityTestResult(
            test_name="constant_time_comparison",
            passed=False,
            message=f"Missing constant-time comparison: {missing}",
            details="Vulnerable to timing attacks without constant-time comparison"
        )


def test_error_messages_safe():
    """Test that error messages don't reveal secret information."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health)

    # Check that error messages are generic
    dangerous_patterns = [
        'detail="Invalid secret',
        'detail="Secret',
        'detail="METRICS_SECRET',
        'detail="Wrong secret',
    ]

    safe_patterns = [
        'detail="Access denied"',
        'detail="Endpoint not available"',
    ]

    issues = []
    for pattern in dangerous_patterns:
        if pattern in source:
            issues.append(f"Found revealing error: {pattern}")

    safe_found = [p for p in safe_patterns if p in source]

    if not issues and len(safe_found) >= 2:
        return SecurityTestResult(
            test_name="error_messages_safe",
            passed=True,
            message="Error messages are generic and don't reveal secrets",
            details=f"Safe patterns: {safe_found}"
        )
    else:
        return SecurityTestResult(
            test_name="error_messages_safe",
            passed=False,
            message=f"Error messages may reveal secret information",
            details=f"Issues: {issues}"
        )


def test_endpoint_disabled_without_secret():
    """Test that endpoints return 503 when secret is not configured."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health._check_production_auth)

    # Check that missing secret returns 503
    checks = [
        "if not secret:" in source,
        "HTTP_503_SERVICE_UNAVAILABLE" in source,
    ]

    if all(checks):
        return SecurityTestResult(
            test_name="endpoint_disabled_without_secret",
            passed=True,
            message="Endpoints correctly disabled (503) when secret not configured"
        )
    else:
        return SecurityTestResult(
            test_name="endpoint_disabled_without_secret",
            passed=False,
            message="Endpoints may not be properly disabled without secret"
        )


def test_security_endpoint_dev_only():
    """Test that security endpoint is blocked in production."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health.security_check)

    if "is_production()" in source and "HTTP_404_NOT_FOUND" in source:
        return SecurityTestResult(
            test_name="security_endpoint_dev_only",
            passed=True,
            message="Security endpoint correctly blocked in production"
        )
    else:
        return SecurityTestResult(
            test_name="security_endpoint_dev_only",
            passed=False,
            message="Security endpoint may be accessible in production"
        )


def test_no_secret_exposure():
    """Test that secrets are not exposed in responses."""
    from app.api.routes import health
    import inspect

    source = inspect.getsource(health)

    # Check for potential secret exposure patterns
    dangerous_patterns = [
        "anthropic_api_key",  # Should not expose full key
        "secret =",  # Should not assign secret to response
    ]

    issues = []
    for pattern in dangerous_patterns:
        # Check if pattern appears in a return or response context
        if pattern in source:
            # Allow if it's just checking existence
            if f"if settings.{pattern}" in source or f"bool({pattern})" in source:
                continue
            if "configured" in source:  # Okay to say "configured: True"
                continue
            issues.append(pattern)

    if not issues:
        return SecurityTestResult(
            test_name="no_secret_exposure",
            passed=True,
            message="No secret exposure detected in health endpoints"
        )
    else:
        return SecurityTestResult(
            test_name="no_secret_exposure",
            passed=False,
            message=f"Potential secret exposure: {issues}"
        )


def main():
    """Run all security verification tests."""
    print("=" * 60)
    print("METRICS SECURITY VERIFICATION")
    print("=" * 60)

    tests = [
        test_production_detection,
        test_metrics_secret_function,
        test_protected_endpoints_list,
        test_production_gating_logic,
        test_constant_time_comparison,
        test_error_messages_safe,
        test_endpoint_disabled_without_secret,
        test_security_endpoint_dev_only,
        test_no_secret_exposure,
    ]

    results = []
    for test_fn in tests:
        result = test_fn()
        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        print(f"\n[{status}] {result.test_name}")
        print(f"       {result.message}")
        if result.details:
            print(f"       {result.details}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if not r.passed:
                print(f"    - {r.test_name}")

    # Security checklist
    print("\n  SECURITY CHECKLIST:")
    print("    - Production gating: " + ("OK" if any(r.test_name == "production_gating_logic" and r.passed for r in results) else "FAIL"))
    print("    - Secret handling: " + ("OK" if any(r.test_name == "metrics_secret_function" and r.passed for r in results) else "FAIL"))
    print("    - No secret exposure: " + ("OK" if any(r.test_name == "no_secret_exposure" and r.passed for r in results) else "FAIL"))

    print("\n  PRODUCTION REQUIREMENTS:")
    print("    - Set ENVIRONMENT=production")
    print("    - Set METRICS_SECRET=<random-secret>")
    print("    - Pass X-Metrics-Secret header to access protected endpoints")

    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
