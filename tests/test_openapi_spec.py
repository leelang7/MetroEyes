"""OpenAPI 3.0 spec 검증 — 9 REST endpoint + 6 type incident enum."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "openapi.yaml"


def test_openapi_loads() -> None:
    """yaml.safe_load 통과 + 최상위 필드 정상."""
    with SPEC.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    assert spec.get("openapi", "").startswith("3."), "OpenAPI 3.x spec must declare openapi: 3.x"
    assert "info" in spec
    assert "paths" in spec


def test_required_endpoints() -> None:
    """9 REST endpoint + /api/docs UI = 10 path 모두 존재."""
    with SPEC.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    paths = spec["paths"]
    required = {
        "/health",
        "/api/v1/roi_curve",
        "/api/v1/impact",
        "/api/v1/incidents",
        "/api/v1/dispersion",
        "/api/v1/od_asymmetry",
        "/api/v1/transfer_priority",
        "/api/v1/policy_summary",
        "/api/openapi.yaml",
    }
    missing = required - set(paths.keys())
    assert not missing, f"missing endpoints: {missing}"


def test_incident_enum_has_idea_7_8() -> None:
    """IncidentEvent enum에 IDEA-7/8 (priority_seat / bottleneck) 포함 검증."""
    with SPEC.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    schemas = spec.get("components", {}).get("schemas", {})
    # search for any schema property containing the 6-type enum
    found = False
    for sname, schema in schemas.items():
        props = (schema or {}).get("properties", {}) or {}
        for pname, pdef in props.items():
            if isinstance(pdef, dict) and pdef.get("enum"):
                e = pdef["enum"]
                if "priority_seat" in e and "bottleneck" in e:
                    found = True
                    assert "emergency" in e and "suspicious" in e and "lost" in e and "free_ride" in e, \
                        f"{sname}.{pname} enum missing legacy types: {e}"
    assert found, "no enum with both priority_seat and bottleneck — IDEA-7/8 not in spec"


def test_policy_summary_has_incident_breakdown() -> None:
    """/api/v1/policy_summary 응답이 incident_breakdown 6 type properties 포함."""
    with SPEC.open(encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    paths = spec["paths"]
    ps = paths.get("/api/v1/policy_summary", {})
    schema = (
        ps.get("get", {})
        .get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )
    props = (schema or {}).get("properties", {}) or {}
    ib = props.get("incident_breakdown", {})
    ib_props = (ib or {}).get("properties", {}) or {}
    for k in ("emergency", "suspicious", "lost", "free_ride", "priority_seat", "bottleneck"):
        assert k in ib_props, f"incident_breakdown missing {k}: {list(ib_props.keys())}"
