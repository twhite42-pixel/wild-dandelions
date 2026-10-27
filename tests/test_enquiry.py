"""Tests for the 'work with me' form.

The thing that matters here: a real person fills in the form and Torie
actually gets the email. These tests swap the real Gmail sender for a fake
one that just records what it was asked to send, so nothing leaves the room.
"""

import pytest

from app import create_app


class FakeSender:
    """Stands in for Gmail. Records calls instead of sending."""

    def __init__(self, blow_up=False):
        self.sent = []
        self.blow_up = blow_up

    def __call__(self, message):
        if self.blow_up:
            raise RuntimeError("gmail said no")
        self.sent.append(message)


@pytest.fixture
def sender():
    return FakeSender()


@pytest.fixture
def client(sender):
    app = create_app({"TESTING": True, "SEND_EMAIL": sender})
    return app.test_client()


def good_payload(**overrides):
    payload = {
        "name": "Sam Rivera",
        "email": "sam@example.com",
        "reason": "custom",
        "message": "I would love a custom pair in green for my sister's birthday.",
        "website": "",  # honeypot, left empty by real humans
    }
    payload.update(overrides)
    return payload


# --- the page itself -------------------------------------------------------


def test_homepage_loads_and_shows_the_products(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Wild Dandelions" in body
    assert "Sunset Marble" in body
    assert "Blush Chain" in body


def test_homepage_renders_every_product_in_the_json(client):
    import json
    from pathlib import Path

    data = json.loads(Path("products.json").read_text())
    body = client.get("/").get_data(as_text=True)
    for product in data["products"]:
        assert product["name"] in body


# --- the happy path --------------------------------------------------------


def test_valid_enquiry_is_accepted(client):
    res = client.post("/api/enquiry", json=good_payload())
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_valid_enquiry_sends_exactly_one_email(client, sender):
    client.post("/api/enquiry", json=good_payload())
    assert len(sender.sent) == 1


def test_email_goes_to_torie(client, sender):
    client.post("/api/enquiry", json=good_payload())
    assert sender.sent[0]["To"] == "toriewhite9@gmail.com"


def test_reply_goes_back_to_the_person_who_wrote_in(client, sender):
    """So Torie can just hit Reply instead of copying the address out."""
    client.post("/api/enquiry", json=good_payload())
    assert sender.sent[0]["Reply-To"] == "Sam Rivera <sam@example.com>"


def test_subject_says_who_it_is_from_and_what_they_want(client, sender):
    client.post("/api/enquiry", json=good_payload())
    subject = sender.sent[0]["Subject"]
    assert "Sam Rivera" in subject
    assert "Custom order" in subject


def test_body_contains_their_message_and_details(client, sender):
    client.post("/api/enquiry", json=good_payload())
    body = sender.sent[0].get_content()
    assert "custom pair in green" in body
    assert "sam@example.com" in body


def test_a_named_piece_is_included_when_they_asked_about_one(client, sender):
    client.post("/api/enquiry", json=good_payload(piece="Coral Swirl"))
    assert "Coral Swirl" in sender.sent[0].get_content()


# --- things people get wrong ----------------------------------------------


@pytest.mark.parametrize(
    "bad, field",
    [
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"email": ""}, "email"),
        ({"email": "not-an-email"}, "email"),
        ({"email": "missing@tld"}, "email"),
        ({"message": ""}, "message"),
        ({"message": "   "}, "message"),
    ],
)
def test_bad_input_is_rejected_with_a_message_naming_the_field(client, bad, field):
    res = client.post("/api/enquiry", json=good_payload(**bad))
    assert res.status_code == 400
    assert field in res.get_json()["error"].lower()


def test_nothing_is_emailed_when_the_form_is_invalid(client, sender):
    client.post("/api/enquiry", json=good_payload(email="nope"))
    assert sender.sent == []


def test_overlong_message_is_rejected(client):
    res = client.post("/api/enquiry", json=good_payload(message="x" * 5001))
    assert res.status_code == 400
    assert "long" in res.get_json()["error"].lower()


def test_request_with_no_json_at_all_is_rejected(client):
    res = client.post("/api/enquiry", data="hello", content_type="text/plain")
    assert res.status_code == 400


# --- spam ------------------------------------------------------------------


def test_bot_filling_the_hidden_field_is_silently_dropped(client, sender):
    """Bots fill every field. Humans never see this one. We lie and say ok
    so the bot does not retry, but no email is sent."""
    res = client.post("/api/enquiry", json=good_payload(website="buy-cheap-pills"))
    assert res.status_code == 200
    assert sender.sent == []


# --- when Gmail is having a bad day ---------------------------------------


def test_sender_failure_returns_a_helpful_error_not_a_crash():
    app = create_app({"TESTING": True, "SEND_EMAIL": FakeSender(blow_up=True)})
    res = app.test_client().post("/api/enquiry", json=good_payload())
    assert res.status_code == 502
    error = res.get_json()["error"]
    assert "toriewhite9@gmail.com" in error, "tell them how to reach her anyway"


def test_missing_credentials_is_reported_clearly():
    """If .env was never filled in, say so plainly rather than failing oddly."""
    app = create_app({"TESTING": True, "GMAIL_ADDRESS": "", "GMAIL_APP_PASSWORD": ""})
    res = app.test_client().post("/api/enquiry", json=good_payload())
    assert res.status_code == 503
    error = res.get_json()["error"].lower()
    assert "set up" in error
    assert "toriewhite9@gmail.com" in error, "tell them how to reach her anyway"
