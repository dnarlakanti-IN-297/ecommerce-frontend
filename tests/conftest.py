"""Shared pytest fixtures for the ecommerce-frontend test suite.

The frontend is a thin Flask proxy over the backend API - api_request()
in app.py is the only place it talks to the backend - so tests stub
`requests.request` at that boundary via the mock_backend fixture instead
of requiring a live backend service.
"""
import os

import pytest

os.environ.setdefault('ROX_SDK_KEY', '')  # feature flags fail soft to their coded defaults

from app import app as flask_app  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    def json(self):
        return self._json_data


class MockBackend:
    """Records every call made through app.requests.request and replays
    whichever FakeResponse the test has assigned to .response."""

    def __init__(self):
        self.response = FakeResponse(200, [])
        self.calls = []

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append({'method': method, 'url': url, 'headers': headers, 'kwargs': kwargs})
        return self.response


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_backend(monkeypatch):
    backend = MockBackend()
    monkeypatch.setattr('app.requests.request', backend.request)
    return backend
