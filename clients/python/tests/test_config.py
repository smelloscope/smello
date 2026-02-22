"""Tests for smello.config.SmelloConfig."""

import pytest
from smello.config import SmelloConfig


@pytest.fixture()
def default_config():
    return SmelloConfig(server_url="http://test:5110")


@pytest.fixture()
def selective_config():
    return SmelloConfig(
        server_url="http://test:5110",
        capture_all=False,
        capture_hosts=["api.stripe.com"],
    )


def test_capture_all_by_default(default_config):
    assert default_config.should_capture("api.stripe.com") is True
    assert default_config.should_capture("example.com") is True


def test_ignore_hosts():
    config = SmelloConfig(
        server_url="http://test:5110", ignore_hosts=["localhost", "127.0.0.1"]
    )
    assert config.should_capture("localhost") is False
    assert config.should_capture("127.0.0.1") is False
    assert config.should_capture("api.stripe.com") is True


def test_capture_specific_hosts_only(selective_config):
    assert selective_config.should_capture("api.stripe.com") is True
    assert selective_config.should_capture("api.openai.com") is False


def test_ignore_takes_precedence_over_capture_hosts():
    config = SmelloConfig(
        server_url="http://test:5110",
        capture_all=False,
        capture_hosts=["api.stripe.com"],
        ignore_hosts=["api.stripe.com"],
    )
    assert config.should_capture("api.stripe.com") is False


def test_ignore_takes_precedence_over_capture_all():
    config = SmelloConfig(
        server_url="http://test:5110",
        capture_all=True,
        ignore_hosts=["secret.internal"],
    )
    assert config.should_capture("secret.internal") is False
    assert config.should_capture("anything.else") is True
