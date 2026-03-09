"""Unit tests for the risk scoring engine."""

import pytest
from processing.score_tracts import (
    WEIGHTS,
    compute_composite_score,
)


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_composite_score_all_zero():
    score = compute_composite_score(0.0, 0.0, 0.0, 0.0)
    assert score == 0.0


def test_composite_score_all_one():
    score = compute_composite_score(1.0, 1.0, 1.0, 1.0)
    assert score == 1.0


def test_composite_score_clamps_to_range():
    # Even with out-of-range inputs, output must be [0, 1]
    score = compute_composite_score(2.0, 2.0, 2.0, 2.0)
    assert 0.0 <= score <= 1.0


def test_composite_score_weighted():
    # Only flood risk = 1.0, others = 0
    score = compute_composite_score(flood=1.0, seismic=0.0, storm=0.0, svi=0.0)
    assert abs(score - WEIGHTS["flood"]) < 1e-9


def test_composite_score_precision():
    score = compute_composite_score(0.5, 0.5, 0.5, 0.5)
    # Should be 0.5 since all components equal
    assert abs(score - 0.5) < 1e-4
