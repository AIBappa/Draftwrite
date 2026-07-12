#!/usr/bin/env python3
"""Test the _build_question_lookup function with actual frontend structure."""
import json
import sys
import os

# Add parent directory so we can import exporter.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from exporter import _build_question_lookup

# Simulate the actual frontend structure
test_questions = {
    'deliverables': [
        {
            'id': 'section_basics',
            'items': [
                {'id': 'D1.1', 'type': 'manual', 'desc': 'Product name'},
                {'id': 'D1.2.3.1', 'type': 'yesno', 'desc': 'Will you have a normal user who only looks at reading data?',
                 'followUpYes': [{'id': 'D1.2.3.1a', 'type': 'manual', 'desc': 'Describe what read-only users will see and do.'}]}
            ]
        }
    ],
    'infrastructure': {
        'items': [
            {'id': 'D1.6.1.1', 'type': 'yesno', 'desc': 'Webapp for normal read-only and paid/premium users?',
             'infraFollowUps': [
                 {'id': 'D1.6.1.2', 'type': 'manual', 'desc': 'Where will it be hosted?'},
                 {'id': 'D1.6.1.3', 'type': 'manual', 'desc': 'What language is expected to be used?'}
             ]},
        ]
    },
    'external': {
        'items': [
            {'id': 'D3.1', 'type': 'yesno', 'desc': 'Will the external products interface with the product?'},
        ]
    },
    'dynamicTemplates': [
        {'template': 'D1.4.2.{n}', 'type': 'manual', 'desc': 'Name of function {n}'}
    ]
}

lookup = _build_question_lookup(test_questions)
print("Question lookup results:")
for key, val in sorted(lookup.items()):
    print(f"  {key:15s} -> {val[:60]}..." if len(val) > 60 else f"  {key:15s} -> {val}")

# Test that it matches the keys we saw in the PDF
expected_keys = ['D1.1', 'D1.2.3.1', 'D1.2.3.1a', 'D1.6.1.1', 'D1.6.1.2', 'D1.6.1.3', 'D3.1']
print("\nChecking expected keys:")
for k in expected_keys:
    status = "FOUND" if k in lookup else "MISSING"
    print(f"  {k}: {status}")

# Real pytest assertions
assert lookup is not None, "Lookup should not be None"
for k in expected_keys:
    assert k in lookup, f"Expected key '{k}' missing from lookup"

# Verify specific descriptions
assert lookup['D1.1'] == 'Product name', f"Expected 'Product name', got '{lookup.get('D1.1')}'"
assert lookup['D1.2.3.1a'] == 'Describe what read-only users will see and do.', \
    f"Follow-up description mismatch: '{lookup.get('D1.2.3.1a')}'"

# Verify template key is stored (but not directly resolvable via exact match)
assert '__template__D1.4.2.{n}' in lookup, "Template key should be stored"

print("\n✅ All assertions passed!")