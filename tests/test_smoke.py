"""Smoke test: vérifie que le package est importable et installé correctement."""

import adsb_weather


def test_package_importable():
    assert adsb_weather.__name__ == "adsb_weather"
