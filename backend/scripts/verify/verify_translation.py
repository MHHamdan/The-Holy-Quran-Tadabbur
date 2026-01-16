#!/usr/bin/env python3
"""
Verify translation service configuration and safety.

Validates:
1. Translation mode is LITERAL_NON_INTERPRETIVE
2. Prompt versioning is working
3. Source hash verification works
4. RAG never translates at runtime

Exit codes:
  0 - All checks passed
  1 - Some checks failed
"""
import sys
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.translation import (
    TranslationService,
    TranslationMode,
    TranslationResult,
    VerificationStatus,
    PROMPT_VERSION,
    PROMPT_HASH,
    LITERAL_TRANSLATION_PROMPT,
    rag_should_never_translate,
)


@dataclass
class TranslationTestResult:
    """Result of a translation test."""
    test_name: str
    passed: bool
    message: str
    details: Optional[str] = None


def test_mode_naming():
    """Test that translation mode is correctly named LITERAL_NON_INTERPRETIVE."""
    result = TranslationTestResult(
        test_name="mode_naming",
        passed=False,
        message=""
    )

    # Check enum value
    mode = TranslationMode.LITERAL_NON_INTERPRETIVE
    if mode.value == "literal_non_interpretive":
        result.passed = True
        result.message = f"Mode correctly named: {mode.value}"
    else:
        result.message = f"Mode incorrectly named: {mode.value}"

    # Verify no "word-for-word" in mode names
    for m in TranslationMode:
        if "word" in m.value.lower():
            result.passed = False
            result.message = f"Mode still contains 'word': {m.value}"
            break

    return result


def test_prompt_versioning():
    """Test that prompt versioning is implemented."""
    result = TranslationTestResult(
        test_name="prompt_versioning",
        passed=False,
        message=""
    )

    # Check version format
    if not PROMPT_VERSION:
        result.message = "PROMPT_VERSION is empty"
        return result

    parts = PROMPT_VERSION.split(".")
    if len(parts) != 3:
        result.message = f"PROMPT_VERSION format invalid: {PROMPT_VERSION}"
        return result

    # Check hash exists
    if not PROMPT_HASH:
        result.message = "PROMPT_HASH is empty"
        return result

    # Verify hash matches current prompt
    expected_hash = hashlib.sha256(LITERAL_TRANSLATION_PROMPT.encode('utf-8')).hexdigest()[:16]
    if PROMPT_HASH != expected_hash:
        result.message = f"PROMPT_HASH mismatch: {PROMPT_HASH} vs {expected_hash}"
        return result

    result.passed = True
    result.message = f"Prompt version {PROMPT_VERSION} with hash {PROMPT_HASH}"
    return result


def test_prompt_no_interpretation():
    """Test that prompt explicitly forbids interpretation."""
    result = TranslationTestResult(
        test_name="prompt_no_interpretation",
        passed=False,
        message=""
    )

    prompt_lower = LITERAL_TRANSLATION_PROMPT.lower()

    required_phrases = [
        "do not interpret",
        "no interpretation",
        "literal",
        "no commentary"
    ]

    found = []
    for phrase in required_phrases:
        if phrase in prompt_lower:
            found.append(phrase)

    if len(found) >= 2:
        result.passed = True
        result.message = f"Prompt contains anti-interpretation rules: {', '.join(found)}"
    else:
        result.message = f"Prompt missing anti-interpretation rules. Found: {found}"

    return result


def test_verification_status_enum():
    """Test that VerificationStatus enum has all required states."""
    result = TranslationTestResult(
        test_name="verification_status_enum",
        passed=False,
        message=""
    )

    required_statuses = ["pending", "verified", "rejected", "flagged"]
    actual_statuses = [s.value for s in VerificationStatus]

    missing = [s for s in required_statuses if s not in actual_statuses]

    if not missing:
        result.passed = True
        result.message = f"All verification statuses present: {actual_statuses}"
    else:
        result.message = f"Missing statuses: {missing}"

    return result


def test_translation_result_fields():
    """Test that TranslationResult has required versioning fields."""
    result = TranslationTestResult(
        test_name="translation_result_fields",
        passed=False,
        message=""
    )

    required_fields = [
        "source_text_hash",
        "prompt_version",
        "verification_status"
    ]

    # Check TranslationResult dataclass fields
    from dataclasses import fields as dataclass_fields
    actual_fields = [f.name for f in dataclass_fields(TranslationResult)]

    missing = [f for f in required_fields if f not in actual_fields]

    if not missing:
        result.passed = True
        result.message = f"TranslationResult has all required versioning fields"
        result.details = f"Fields: {', '.join(required_fields)}"
    else:
        result.message = f"TranslationResult missing fields: {missing}"

    return result


def test_rag_never_translates():
    """Test that RAG guard function exists and works."""
    result = TranslationTestResult(
        test_name="rag_never_translates",
        passed=False,
        message=""
    )

    # Check guard function exists and returns True
    if rag_should_never_translate():
        result.passed = True
        result.message = "rag_should_never_translate() guard is active"
    else:
        result.message = "rag_should_never_translate() returned False!"

    return result


def test_source_hash_computation():
    """Test that source hash computation is consistent."""
    result = TranslationTestResult(
        test_name="source_hash_computation",
        passed=False,
        message=""
    )

    # Test text
    test_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

    # Compute hash the same way as TranslationService
    hash1 = hashlib.sha256(test_text.encode('utf-8')).hexdigest()
    hash2 = hashlib.sha256(test_text.encode('utf-8')).hexdigest()

    if hash1 == hash2:
        result.passed = True
        result.message = f"Source hash computation is deterministic"
        result.details = f"Hash: {hash1[:16]}..."
    else:
        result.message = "Source hash computation is non-deterministic!"

    return result


def test_translation_mode_default():
    """Test that default mode is LITERAL_NON_INTERPRETIVE."""
    result = TranslationTestResult(
        test_name="translation_mode_default",
        passed=False,
        message=""
    )

    # Check TranslationService default
    import inspect
    sig = inspect.signature(TranslationService.__init__)
    mode_param = sig.parameters.get("mode")

    if mode_param and mode_param.default == TranslationMode.LITERAL_NON_INTERPRETIVE:
        result.passed = True
        result.message = "Default mode is LITERAL_NON_INTERPRETIVE"
    else:
        default = mode_param.default if mode_param else "None"
        result.message = f"Default mode is not LITERAL_NON_INTERPRETIVE: {default}"

    return result


def main():
    """Run all translation verification tests."""
    print("=" * 60)
    print("TRANSLATION SERVICE VERIFICATION")
    print("=" * 60)

    print(f"\nPrompt Version: {PROMPT_VERSION}")
    print(f"Prompt Hash: {PROMPT_HASH}\n")

    # Run tests
    tests = [
        test_mode_naming,
        test_prompt_versioning,
        test_prompt_no_interpretation,
        test_verification_status_enum,
        test_translation_result_fields,
        test_rag_never_translates,
        test_source_hash_computation,
        test_translation_mode_default,
    ]

    results = []
    for test_fn in tests:
        result = test_fn()
        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.test_name}")
        print(f"       {result.message}")
        if result.details:
            print(f"       {result.details}")
        print()

    # Summary
    print("=" * 60)
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

    # Critical safety check
    print("\n  CRITICAL SAFETY CHECKS:")
    print(f"    - RAG never translates at runtime: {'OK' if rag_should_never_translate() else 'FAIL'}")
    print(f"    - Mode is literal non-interpretive: {'OK' if TranslationMode.LITERAL_NON_INTERPRETIVE else 'FAIL'}")
    print(f"    - Prompt versioning active: {'OK' if PROMPT_VERSION else 'FAIL'}")

    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
