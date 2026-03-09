"""Unit tests for NOAA NWS alert ingestion."""

from datetime import datetime, timezone

import pytest
from ingestion.noaa.ingest_alerts import (
    _parse_datetime,
    _parse_geometry,
)


# ── _parse_datetime ──

def test_parse_datetime_iso_z():
    result = _parse_datetime("2025-06-01T12:00:00Z")
    assert isinstance(result, datetime)
    assert result.tzinfo is None  # stored as UTC naive
    assert result.year == 2025
    assert result.hour == 12


def test_parse_datetime_with_offset():
    result = _parse_datetime("2025-06-01T07:00:00-05:00")
    assert isinstance(result, datetime)
    assert result.hour == 12  # converted to UTC


def test_parse_datetime_none():
    assert _parse_datetime(None) is None


def test_parse_datetime_invalid():
    assert _parse_datetime("not-a-date") is None


# ── _parse_geometry ──

def test_parse_geometry_polygon():
    feature = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-97.0, 35.0],
                [-96.0, 35.0],
                [-96.0, 36.0],
                [-97.0, 36.0],
                [-97.0, 35.0],
            ]]
        }
    }
    result = _parse_geometry(feature)
    assert result is not None
    assert result.startswith("SRID=4326;")
    assert "MULTIPOLYGON" in result


def test_parse_geometry_multipolygon():
    feature = {
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [[[
                [-97.0, 35.0],
                [-96.0, 35.0],
                [-96.0, 36.0],
                [-97.0, 36.0],
                [-97.0, 35.0],
            ]]]
        }
    }
    result = _parse_geometry(feature)
    assert result is not None
    assert "MULTIPOLYGON" in result


def test_parse_geometry_null():
    feature = {"geometry": None}
    assert _parse_geometry(feature) is None


def test_parse_geometry_missing():
    feature = {}
    assert _parse_geometry(feature) is None


def test_parse_geometry_point_returns_none():
    """Point geometry cannot be cast to MultiPolygon — should return None."""
    feature = {
        "geometry": {
            "type": "Point",
            "coordinates": [-97.0, 35.0]
        }
    }
    assert _parse_geometry(feature) is None
