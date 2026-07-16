"""Tests for the CloudBees Unify feature-flag gated behavior.

These don't require a real ROX_SDK_KEY / Unify connection - conftest.py
leaves ROX_SDK_KEY unset, so the SDK fails soft and every flag stays on
its coded default (see feature_flags.py). Tests monkeypatch the flag's
is_enabled() directly to exercise both the on and off code paths
deterministically, rather than depending on Unify's actual live state.
"""
from conftest import FakeResponse

import app as app_module


def test_promo_banner_hidden_when_flag_off(client, mock_backend, monkeypatch):
    monkeypatch.setattr(app_module.flags.show_promo_banner, 'is_enabled', lambda: False)
    mock_backend.response = FakeResponse(200, [])
    resp = client.get('/')
    assert b'Limited time offer' not in resp.data


def test_promo_banner_shown_when_flag_on(client, mock_backend, monkeypatch):
    monkeypatch.setattr(app_module.flags.show_promo_banner, 'is_enabled', lambda: True)
    mock_backend.response = FakeResponse(200, [])
    resp = client.get('/')
    assert b'Limited time offer' in resp.data
