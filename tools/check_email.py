"""Save your Gmail app password and prove it actually works.

Run it with:   ./.venv/bin/python tools/check_email.py

It asks for the app password (nothing is shown as you type), writes it to
.env, then sends you a real test message so you know it works before any
customer relies on it.
"""

import smtplib
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import TORIE_EMAIL, build_message, gmail_sender  # noqa: E402

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def save(address: str, password: str) -> None:
    ENV_FILE.write_text(
        "# Created by tools/check_email.py. Keep this file private.\n"
        f"GMAIL_ADDRESS={address}\n"
        f"GMAIL_APP_PASSWORD={password}\n"
    )
    ENV_FILE.chmod(0o600)


def main() -> int:
    print("\n  Gmail app password setup")
    print("  " + "-" * 46)
    print("  Not your normal Gmail password - the 16-letter one from")
    print("  https://myaccount.google.com/apppasswords\n")

    password = getpass("  Paste it here (it stays hidden): ").replace(" ", "").strip()
    if not password:
        print("\n  Nothing entered. Stopping.\n")
        return 1
    if len(password) != 16:
        print(f"\n  That's {len(password)} characters - app passwords are 16.")
        print("  Carry on anyway? Press Enter to try it, or Control-C to stop.")
        input()

    print("\n  Talking to Gmail...")
    try:
        send = gmail_sender(TORIE_EMAIL, password)
        test = build_message({
            "name": "Your website",
            "email": TORIE_EMAIL,
            "reason": "hello",
            "message": (
                "This is a test from your contact form setup.\n\n"
                "If you are reading this, the form works. Real enquiries will "
                "look like this, with the sender's address in the Reply-To "
                "field so you can just hit Reply."
            ),
        })
        send(test)
    except smtplib.SMTPAuthenticationError:
        print("\n  Gmail refused that password.")
        print("  Two usual reasons:")
        print("    - it was typed or pasted slightly wrong")
        print("    - 2-Step Verification is off, so the password isn't valid")
        print("  Nothing was saved. Try again when you have a fresh one.\n")
        return 1
    except Exception as problem:  # noqa: BLE001
        print(f"\n  Could not send: {problem}")
        print("  Nothing was saved.\n")
        return 1

    save(TORIE_EMAIL, password)
    print("\n  Sent. Check " + TORIE_EMAIL + " - a test message is waiting.")
    print("  Saved to .env, so your local site can send mail now.")
    print("\n  Next: add the same password to Vercel so the live site can")
    print("  send too. README.md has the steps.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
