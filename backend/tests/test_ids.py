"""Company_ID contract tests: frozen format, dots kept, no NVIDIA confusion."""
from app.services.ids import format_company_id, is_valid_company_id, normalize_company_id, parse_company_id


def test_parse_us():
    cid = parse_company_id("US:MMM:US")
    assert cid is not None
    assert cid.format() == "US:MMM:US"


def test_parse_ca_keeps_dots():
    cid = parse_company_id("CA:BN:TSX")
    assert cid is not None
    assert cid.format() == "CA:BN:TSX"


def test_na_is_national_bank_not_nvidia():
    cid = parse_company_id("CA:NA:TSX")
    assert cid is not None
    assert cid.country == "CA"
    assert cid.ticker == "NA"
    assert cid.exchange == "TSX"
    assert cid.format() == "CA:NA:TSX"


def test_normalize_loose_exchange_suffixes():
    assert normalize_company_id("US:AES:NYSE") == "US:AES:US"
    assert normalize_company_id("US:APA:NASDAQ") == "US:APA:US"
    assert normalize_company_id("CA:NA:TO") == "CA:NA:TSX"
    assert normalize_company_id("US:MMM:US") == "US:MMM:US"


def test_format_from_country_ticker():
    assert format_company_id("US", "brk.b") == "US:BRK.B:US"
    assert format_company_id("CA", "bn") == "CA:BN:TSX"


def test_invalid_ids_rejected():
    assert parse_company_id("NVIDIA") is None
    assert parse_company_id("US:MMM") is None
    assert parse_company_id("XX:MMM:US") is None
    assert normalize_company_id("") is None
    assert normalize_company_id(None) is None
    assert not is_valid_company_id("CA:BN:NYSE")


def test_round_trip():
    for raw in ("US:MMM:US", "CA:BN:TSX", "CA:NA:TSX", "US:BRK.B:US"):
        cid = parse_company_id(raw)
        assert cid is not None and cid.format() == raw
