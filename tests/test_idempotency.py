"""Tests for the idempotency module."""

from app.idempotency import canonical_json, idempotency_key, _normalize


def test_canonical_json_sorts_keys():
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b


def test_canonical_json_normalizes_floats():
    a = canonical_json({"val": 12.0})
    b = canonical_json({"val": 12})
    assert a == b


def test_normalize_nested():
    result = _normalize({"a": [1.0, 2.0, {"b": 3.0}]})
    assert result == {"a": [1, 2, {"b": 3}]}


def test_idempotency_key_deterministic():
    k1 = idempotency_key("run_abc", 1, "apply_for_loan", {"customer_id": 1, "amount": 50000})
    k2 = idempotency_key("run_abc", 1, "apply_for_loan", {"amount": 50000, "customer_id": 1})
    assert k1 == k2


def test_idempotency_key_different_for_different_runs():
    k1 = idempotency_key("run_abc", 1, "apply_for_loan", {"customer_id": 1})
    k2 = idempotency_key("run_xyz", 1, "apply_for_loan", {"customer_id": 1})
    assert k1 != k2


def test_idempotency_key_different_for_different_steps():
    k1 = idempotency_key("run_abc", 1, "apply_for_loan", {"customer_id": 1})
    k2 = idempotency_key("run_abc", 2, "apply_for_loan", {"customer_id": 1})
    assert k1 != k2
