#!/usr/bin/env python3
"""
Theme Labels Validation Script

Validates theme_labels.json for CI/CD pipelines.

Checks:
1. File exists and is valid JSON
2. All required fields present for each theme
3. No empty labels
4. All theme IDs follow naming convention (theme_*)
5. All categories are valid

Exit codes:
- 0: All validations passed
- 1: Validation failed
"""
import json
import sys
from pathlib import Path

# Expected categories
VALID_CATEGORIES = {
    'aqidah', 'iman', 'ibadat',
    'akhlaq_fardi', 'akhlaq_ijtima',
    'muharramat', 'sunan_ilahiyyah',
}

# Required fields for each label
REQUIRED_FIELDS = ['title_ar', 'title_en', 'category', 'slug']

def validate_theme_labels(filepath: str) -> tuple[bool, list[str]]:
    """Validate theme_labels.json file."""
    errors = []

    # Check file exists
    path = Path(filepath)
    if not path.exists():
        return False, [f"File not found: {filepath}"]

    # Check valid JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    # Check structure
    if 'labels' not in data:
        return False, ["Missing 'labels' key in root"]

    labels = data['labels']
    if not isinstance(labels, dict):
        return False, ["'labels' must be an object"]

    # Validate each theme
    for theme_id, label in labels.items():
        # Check naming convention
        if not theme_id.startswith('theme_'):
            errors.append(f"Invalid theme ID format: {theme_id} (should start with 'theme_')")

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in label:
                errors.append(f"{theme_id}: missing required field '{field}'")
            elif not label[field] or not str(label[field]).strip():
                errors.append(f"{theme_id}: empty value for '{field}'")

        # Check category validity
        if 'category' in label and label['category'] not in VALID_CATEGORIES:
            errors.append(f"{theme_id}: invalid category '{label['category']}'")

        # Check Arabic labels are actually Arabic
        if 'title_ar' in label:
            title_ar = label['title_ar']
            if title_ar and not any('\u0600' <= c <= '\u06FF' for c in title_ar):
                errors.append(f"{theme_id}: title_ar does not contain Arabic characters")

    return len(errors) == 0, errors


def main():
    """Run validation."""
    # Default path
    script_dir = Path(__file__).parent
    labels_path = script_dir.parent.parent / 'app' / 'data' / 'themes' / 'theme_labels.json'

    # Allow override via command line
    if len(sys.argv) > 1:
        labels_path = Path(sys.argv[1])

    print(f"Validating: {labels_path}")
    print("=" * 60)

    valid, errors = validate_theme_labels(str(labels_path))

    if valid:
        print("All validations passed!")
        # Print summary
        with open(labels_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        labels = data.get('labels', {})
        print(f"\nTotal themes: {len(labels)}")

        # Count by category
        categories = {}
        for label in labels.values():
            cat = label.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        print("\nBy category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")

        return 0
    else:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
