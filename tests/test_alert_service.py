# test_alert_service.py
# Unit tests for alert_service.py pure functions.
# No DB or HTTP needed — runs instantly and in complete isolation.
#
# Coverage:
#   get_zone_status()  — all three bands, exact boundary values
#   is_alert()         — true/false at and around the critical threshold

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from alert_service import get_zone_status, is_alert


# ── get_zone_status ───────────────────────────────────────────────────────────

class TestGetZoneStatus:
    def test_below_warning_is_ok(self):
        assert get_zone_status(0.0) == "ok"
        assert get_zone_status(1.0) == "ok"
        assert get_zone_status(1.99) == "ok"

    def test_exactly_at_warning_threshold_is_warning(self):
        # Boundary: WARNING_THRESHOLD = 2.0
        assert get_zone_status(2.0) == "warning"

    def test_between_thresholds_is_warning(self):
        assert get_zone_status(2.1) == "warning"
        assert get_zone_status(2.49) == "warning"

    def test_exactly_at_critical_threshold_is_critical(self):
        # Boundary: CRITICAL_THRESHOLD = 2.5
        assert get_zone_status(2.5) == "critical"

    def test_above_critical_is_critical(self):
        assert get_zone_status(2.51) == "critical"
        assert get_zone_status(4.0) == "critical"
        assert get_zone_status(99.9) == "critical"

    def test_zero_is_ok(self):
        assert get_zone_status(0.0) == "ok"


# ── is_alert ─────────────────────────────────────────────────────────────────

class TestIsAlert:
    def test_ok_level_is_not_alert(self):
        assert is_alert(1.0) is False

    def test_warning_level_is_not_alert(self):
        assert is_alert(2.2) is False

    def test_just_below_critical_is_not_alert(self):
        assert is_alert(2.499) is False

    def test_exactly_at_critical_is_alert(self):
        assert is_alert(2.5) is True

    def test_above_critical_is_alert(self):
        assert is_alert(2.9) is True
        assert is_alert(4.0) is True
