"""Tests for CTD section numeric ordering."""

from app.services.ctd_ordering import ctd_code_sort_key


def test_ctd_code_sort_key_numeric_order() -> None:
    codes = ["3.2.S.4.10", "3.2.S.4.2", "3.2.S.4.1", None]
    sorted_codes = sorted(codes, key=ctd_code_sort_key)
    assert sorted_codes == ["3.2.S.4.1", "3.2.S.4.2", "3.2.S.4.10", None]
