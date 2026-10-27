"""Wild Dandelions - by Torie White.

A small Flask app that serves the shop page and emails enquiries to Torie.

Run it:      ./.venv/bin/python app.py
Then open:   http://localhost:5050

Port 5050, not the Flask default of 5000, because macOS gives port 5000 to
AirPlay Receiver and it quietly answers every request with "403 Forbidden".
"""

from __future__ import annotations

import json
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

HERE = Path(__file__).parent
PRODUCTS_FILE = HERE / "products.json"

# Images, CSS and the font live under public/ so that Vercel serves them
# straight from its CDN instead of waking Python for every picture.
STATIC_DIR = HERE / "public" / "static"

# Where enquiries land.
TORIE_EMAIL = "toriewhite9@gmail.com"

MAX_MESSAGE_LENGTH = 5000

# Deliberately loose - the only real test of an address is sending to it.
# This just catches obvious typos before we waste a round trip.
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

REASON_LABELS = {
    "custom": "Custom order",
    "commission": "Painting commission",
    "stockist": "Wants to stock Wild Dandelions",
    "hello": "Just saying hi",
}


def load_products() -> list[dict]:
    """Read products.json fresh on every page load.

    Deliberately not cached: Torie edits that file by hand and should see
    her change by refreshing the browser, not by restarting the server.
    """
    try:
        data = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
        return data.get("products", [])
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        # A stray comma shouldn't take the whole site down.
        print(f"\n!! products.json has a typo and was skipped: {exc}\n")
        return []


def build_message(form: dict) -> EmailMessage:
    """Turn a validated form submission into an email ready to send."""
    reason = REASON_LABELS.get(form.get("reason", ""), "Enquiry")
    name = form["name"]

    message = EmailMessage()
    message["Subject"] = f"{reason} from {name} - wilddandelions.com"
    message["To"] = TORIE_EMAIL
    # Reply-To is the whole trick: Torie hits Reply and it goes to them,
    # not back to her own sending address.
    message["Reply-To"] = f"{name} <{form['email']}>"

    lines = [
        f"From:    {name}",
        f"Email:   {form['email']}",
        f"About:   {reason}",
    ]
    if form.get("piece"):
        lines.append(f"Piece:   {form['piece']}")
    lines += ["", "-" * 48, "", form["message"], "", "-" * 48, "",
              "Sent from the contact form on your website."]

    message.set_content("\n".join(lines))
    return message


def gmail_sender(address: str, app_password: str):
    """Return a function that sends an EmailMessage through Gmail."""

    def send(message: EmailMessage) -> None:
        message["From"] = f"Wild Dandelions site <{address}>"
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(address, app_password)
            server.send_message(message)

    return send


def validate(form: dict) -> str | None:
    """Return an error message for the first problem found, or None if fine."""
    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip()
    body = (form.get("message") or "").strip()

    if not name:
        return "Please tell me your name."
    if not email:
        return "Please leave an email so I can write back."
    if not EMAIL_PATTERN.match(email):
        return "That email address doesn't look quite right - mind checking it?"
    if not body:
        return "Please write a message so I know what you're after."
    if len(body) > MAX_MESSAGE_LENGTH:
        return (
            f"That message is a little too long "
            f"({len(body)} characters, the limit is {MAX_MESSAGE_LENGTH})."
        )
    return None


def create_app(config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static",
        template_folder=str(HERE / "templates"),
    )
    # Fingerprint-free filenames, so tell browsers and the CDN to keep
    # them a good while rather than re-fetching on every visit.
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 7

    app.config["GMAIL_ADDRESS"] = os.environ.get("GMAIL_ADDRESS", "")
    app.config["GMAIL_APP_PASSWORD"] = os.environ.get("GMAIL_APP_PASSWORD", "")
    app.config["SEND_EMAIL"] = None  # tests inject a fake here
    if config:
        app.config.update(config)

    @app.route("/")
    def home():
        return render_template("index.html", products=load_products())

    @app.post("/api/enquiry")
    def enquiry():
        form = request.get_json(silent=True)
        if not isinstance(form, dict):
            return jsonify(error="Something went wrong sending the form."), 400

        # Honeypot: a field hidden from humans by CSS. Only bots fill it in.
        # Answer "ok" so the bot stops retrying, but send nothing.
        if (form.get("website") or "").strip():
            return jsonify(ok=True), 200

        problem = validate(form)
        if problem:
            return jsonify(error=problem), 400

        clean = {
            "name": form["name"].strip(),
            "email": form["email"].strip(),
            "message": form["message"].strip(),
            "reason": (form.get("reason") or "").strip(),
            "piece": (form.get("piece") or "").strip(),
        }

        send = app.config["SEND_EMAIL"]
        if send is None:
            address = app.config["GMAIL_ADDRESS"]
            password = app.config["GMAIL_APP_PASSWORD"]
            if not address or not password:
                return jsonify(
                    error="The contact form isn't set up yet. "
                          f"Please email {TORIE_EMAIL} directly."
                ), 503
            send = gmail_sender(address, password)

        try:
            send(build_message(clean))
        except Exception as exc:  # noqa: BLE001 - any failure, same answer
            app.logger.error("Could not send enquiry email: %s", exc)
            return jsonify(
                error="Sorry, the message didn't go through. "
                      f"Please email {TORIE_EMAIL} directly."
            ), 502

        return jsonify(ok=True), 200

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        print("\n  Heads up: no Gmail app password found in .env")
        print("  The site will work, but the contact form can't send mail yet.")
        print("  See README.md for the 2-minute setup.\n")
    print(f"\n  Wild Dandelions is running at  http://localhost:{port}")
    print("  Press Control-C to stop it.\n")
    app.run(debug=True, port=port)
