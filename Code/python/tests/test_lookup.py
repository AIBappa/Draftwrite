#!/usr/bin/env python3
"""Test the _build_question_lookup function with actual frontend structure."""
import json

# Define the function inline to test
def _build_question_lookup(stage1_questions):
    lookup = {}
    if not stage1_questions:
        return lookup
    
    # From STAGE1_PRD_DELIVERABLES (deliverables)
    for section in stage1_questions.get("deliverables", []):
        for item in section.get("items", []):
            qid = item.get("id", "")
            desc = item.get("desc", "")
            if qid and desc:
                lookup[qid] = desc
            # Follow-up questions (yes/no followUpYes)
            for followup in item.get("followUpYes", []):
                fid = followup.get("id", "")
                fdesc = followup.get("desc", "")
                if fid and fdesc:
                    lookup[fid] = fdesc
    
    # From STAGE1_INFRASTRUCTURE_SECTION (infrastructure)
    infra = stage1_questions.get("infrastructure", {})
    for item in infra.get("items", []):
        qid = item.get("id", "")
        desc = item.get("desc", "")
        if qid and desc:
            lookup[qid] = desc
        # Infrastructure follow-ups
        for followup in item.get("infraFollowUps", []):
            fid = followup.get("id", "")
            fdesc = followup.get("desc", "")
            if fid and fdesc:
                lookup[fid] = fdesc
    
    # From STAGE1_EXTERNAL_SECTION (external)
    ext = stage1_questions.get("external", {})
    for item in ext.get("items", []):
        qid = item.get("id", "")
        desc = item.get("desc", "")
        if qid and desc:
            lookup[qid] = desc
    
    # From STAGE1_DYNAMIC_TEMPLATES (dynamic items like function names)
    for tmpl in stage1_questions.get("dynamicTemplates", []):
        template_str = tmpl.get("template", "")
        desc_template = tmpl.get("desc", "")
        if template_str and desc_template:
            lookup[f"__template__{template_str}"] = desc_template
    
    return lookup

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