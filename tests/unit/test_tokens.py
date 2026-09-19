from datetime import timedelta

import pytest

from bastion.auth import tokens
from bastion.auth.tokens import issue_token, read_token
from bastion.config import get_settings
from bastion.db import Access

ACCESS = Access(
    user_id="11111111-1111-1111-1111-111111111111",
    level=2,
    departments=("ENG",),
)


@pytest.fixture
def jwt_secret(monkeypatch):
    monkeypatch.setenv("BASTION_JWT_SECRET", "t" * 40)
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


def test_a_token_round_trips(jwt_secret):
    claims = read_token(issue_token(ACCESS, token_version=0))

    assert claims["sub"] == ACCESS.user_id
    assert claims["ver"] == 0


def test_the_token_carries_no_access_details(jwt_secret):
    claims = read_token(issue_token(ACCESS, token_version=0))

    assert "level" not in claims
    assert "departments" not in claims


def test_a_tampered_token_is_rejected(jwt_secret):
    token = issue_token(ACCESS, token_version=0)
    tampered = token[:-4] + "aaaa"

    assert read_token(tampered) is None


def test_an_expired_token_is_rejected(jwt_secret, monkeypatch):
    monkeypatch.setattr(tokens, "TOKEN_LIFETIME", timedelta(seconds=-1))

    assert read_token(issue_token(ACCESS, token_version=0)) is None


def test_a_short_secret_is_refused(monkeypatch):
    monkeypatch.setenv("BASTION_JWT_SECRET", "too-short")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        issue_token(ACCESS, token_version=0)

    get_settings.cache_clear()