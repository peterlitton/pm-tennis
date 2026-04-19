"""
PM-Tennis Phase 3 attempt 2 — CLOB asset-cap stress test package.

This package is the deliverable authorized by D-018 and scoped by research
document docs/clob_asset_cap_stress_test_research.md v4. It is deployed as a
separate Render service from pm-tennis-api per D-020 / Q2=(b) and D-024
commitment 1. pm-tennis-api's requirements.txt is not modified.

Modules:
    probe           - the D-025 hybrid-probe-first one-slug probe implementation
    slug_selector   - reads meta.json on the persistent disk to pick a fresh
                      probe candidate at runtime
"""

__version__ = "0.1.0-stress-test-h013"
