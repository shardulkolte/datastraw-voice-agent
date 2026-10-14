
from backend.app.services.policies import (
    get_shipping_policy,
    check_return_policy,
    check_damage_policy,
    check_cancellation_policy,
    check_cod_policy,
)


def test_free_shipping_above_499():
    result = get_shipping_policy(500)
    assert result["shipping_fee"] == 0


def test_shipping_fee_below_499():
    result = get_shipping_policy(400)
    assert result["shipping_fee"] == 50


def test_shipping_boundary_is_flagged():
    result = get_shipping_policy(499)
    assert result["status"] == "clarification_required"


def test_return_eligible():
    result = check_return_policy(5, True, True, True)
    assert result["eligible"] is True


def test_return_after_7_days_rejected():
    result = check_return_policy(14, True, True, True)
    assert result["eligible"] is False


def test_damage_requires_photos():
    result = check_damage_policy(24, False)
    assert result["eligible"] is False


def test_damage_after_48_hours_rejected():
    result = check_damage_policy(49, True)
    assert result["eligible"] is False


def test_cancellation_allowed_while_processing():
    result = check_cancellation_policy("Processing")
    assert result["eligible"] is True


def test_cancellation_rejected_out_for_delivery():
    result = check_cancellation_policy("Out for Delivery")
    assert result["eligible"] is False


def test_cod_allowed_within_limit():
    result = check_cod_policy(2500)
    assert result["eligible"] is True


def test_cod_rejected_above_limit():
    result = check_cod_policy(3000)
    assert result["eligible"] is False
