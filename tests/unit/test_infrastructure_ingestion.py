"""Unit tests for HIFLD critical infrastructure ingestion."""

from ingestion.hifld.ingest_infrastructure import (
    STATE_ABBR_TO_FIPS,
    _resolve_county_fips,
    _resolve_state_fips,
)

# ── STATE_ABBR_TO_FIPS ──


def test_state_abbr_mapping_count():
    # 50 states + DC = 51
    assert len(STATE_ABBR_TO_FIPS) == 51


def test_state_abbr_key_states():
    assert STATE_ABBR_TO_FIPS["CA"] == "06"
    assert STATE_ABBR_TO_FIPS["TX"] == "48"
    assert STATE_ABBR_TO_FIPS["NY"] == "36"
    assert STATE_ABBR_TO_FIPS["DC"] == "11"


# ── _resolve_state_fips ──


def test_resolve_state_fips_from_county():
    props = {"COUNTYFIPS": "06037"}
    assert _resolve_state_fips(props) == "06"


def test_resolve_state_fips_from_abbr():
    props = {"STATE": "CA"}
    assert _resolve_state_fips(props) == "06"


def test_resolve_state_fips_from_abbr_with_spaces():
    props = {"STATE": " tx "}
    assert _resolve_state_fips(props) == "48"


def test_resolve_state_fips_none():
    assert _resolve_state_fips({}) is None


def test_resolve_state_fips_county_takes_priority():
    props = {"COUNTYFIPS": "48201", "STATE": "CA"}
    assert _resolve_state_fips(props) == "48"


# ── _resolve_county_fips ──


def test_resolve_county_fips_valid():
    assert _resolve_county_fips({"COUNTYFIPS": "06037"}) == "06037"


def test_resolve_county_fips_zero_padded():
    assert _resolve_county_fips({"COUNTYFIPS": "1001"}) == "01001"


def test_resolve_county_fips_none():
    assert _resolve_county_fips({}) is None
    assert _resolve_county_fips({"COUNTYFIPS": ""}) is None
