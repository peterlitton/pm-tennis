"""
PM-Tennis Phase 3 attempt 2 — CLOB asset-cap stress test package.

This package is the deliverable authorized by D-018 and scoped by research
document docs/clob_asset_cap_stress_test_research.md v4. It is deployed as a
separate Render service from pm-tennis-api per D-020 / Q2=(b) and D-024
commitment 1. pm-tennis-api's requirements.txt is not modified.

Modules:
    probe            - the D-025 hybrid-probe-first one-slug probe implementation
    slug_selector    - reads meta.json on the persistent disk to pick a fresh
                       probe candidate at runtime
    list_candidates  - operator-facing CLI that prints eligible probe
                       candidates one per line. Used from the pm-tennis-api
                       Render Shell to pick a slug for the probe (RB-002 §5.1).
                       Replaces the multi-line pasted snippet that failed
                       twice in the Render Shell at H-015.
"""

__version__ = "0.1.1-stress-test-h016"
