"""Pure helpers of app.core.i18n (no database)."""

from app.core.i18n import parse_accept_language, tr


def test_parse_accept_language():
    assert parse_accept_language(None) == "en"
    assert parse_accept_language("es-ES,es;q=0.9,en;q=0.8") == "es"
    assert parse_accept_language("de-DE,fr;q=0.5,es;q=0.7") == "es"
    assert parse_accept_language("ja, en;q=0") == "en"


def test_french_typography_and_fallbacks():
    assert tr("invalid_json", "fr", error="x") == "JSON non valide : x"
    assert tr("unknown_code", "es") == "unknown_code"
