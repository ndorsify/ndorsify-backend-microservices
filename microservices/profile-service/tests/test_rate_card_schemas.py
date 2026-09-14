"""Validation rules for rate-card payloads — the server is the authority."""
import pytest
from pydantic import ValidationError


def _item(**kw):
    return {"platform": "instagram", "type": "reel", "quantity": 1, **kw}


def _package(**kw):
    return {
        "name": "Single Reel",
        "price": 1600,
        "description": "1 Reel, 30-45s",
        "turnaround_days": 5,
        "visible": True,
        "items": [_item()],
        **kw,
    }


def _card(**kw):
    from app.schemas.rate_cards import RateCardUpdate

    return RateCardUpdate(**{"hidden": False, "packages": [_package()], **kw})


def test_a_valid_card_parses():
    card = _card()
    assert card.packages[0].price == 1600
    assert card.packages[0].items[0].platform == "instagram"


def test_empty_card_is_valid():
    assert _card(packages=[]).packages == []


@pytest.mark.parametrize(
    "override",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 81},
        {"price": 0},
        {"price": 1_000_001},
        {"description": "x" * 501},
        {"turnaround_days": 0},
        {"turnaround_days": 91},
        {"items": []},
        {"items": [_item() for _ in range(11)]},
        {"items": [_item(platform="friendster")]},
        {"items": [_item(type="podcast")]},
        {"items": [_item(quantity=0)]},
        {"items": [_item(quantity=51)]},
    ],
)
def test_invalid_package_is_rejected(override):
    with pytest.raises(ValidationError):
        _card(packages=[_package(**override)])


def test_more_than_ten_packages_is_rejected():
    with pytest.raises(ValidationError):
        _card(packages=[_package() for _ in range(11)])


def test_name_is_trimmed():
    card = _card(packages=[_package(name="  Launch bundle  ")])
    assert card.packages[0].name == "Launch bundle"
