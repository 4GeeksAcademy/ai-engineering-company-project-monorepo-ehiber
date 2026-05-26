import json
from pathlib import Path
from urllib import error, request

from ..core.config import get_settings


class EmailDeliveryError(RuntimeError):
    pass


def send_password_reset_email(*, recipient: str, reset_url: str) -> None:
    settings = get_settings()
    subject = "TrackFlow password reset"
    text_body = (
        "You requested a password reset for your TrackFlow account.\n\n"
        f"Reset your password using this link (valid for {settings.password_reset_expire_minutes} minutes):\n"
        f"{reset_url}\n\n"
        "If you did not request this change, you can ignore this email."
    )
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #12202f;">
        <h2>Reset your TrackFlow password</h2>
        <p>You requested a password reset for your TrackFlow account.</p>
        <p>
          <a href="{reset_url}" style="display:inline-block;padding:12px 18px;background:#005f73;color:#fff;text-decoration:none;border-radius:999px;">
            Reset password
          </a>
        </p>
        <p>This link expires in {settings.password_reset_expire_minutes} minutes.</p>
        <p>If you did not request this change, you can ignore this email.</p>
      </body>
    </html>
    """

    if settings.resend_api_key:
        _send_with_resend(
            api_key=settings.resend_api_key,
            sender=settings.password_reset_from_email,
            recipient=recipient,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )
        return

    _write_dev_email(recipient=recipient, subject=subject, text_body=text_body, reset_url=reset_url)


def _send_with_resend(
    *,
    api_key: str,
    sender: str,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    payload = json.dumps(
        {
            "from": sender,
            "to": [recipient],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        }
    ).encode("utf-8")

    http_request = request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=15) as response:
            if response.status >= 400:
                raise EmailDeliveryError("Unable to send password reset email.")
    except error.HTTPError as exc:
        raise EmailDeliveryError("Unable to send password reset email.") from exc
    except error.URLError as exc:
        raise EmailDeliveryError("Unable to reach the email provider.") from exc


def _write_dev_email(*, recipient: str, subject: str, text_body: str, reset_url: str) -> None:
    settings = get_settings()
    output_dir = Path(settings.dev_email_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "last_password_reset.txt"
    output_path.write_text(
        "\n".join(
            [
                f"To: {recipient}",
                f"Subject: {subject}",
                "",
                text_body,
                "",
                f"Reset URL: {reset_url}",
            ]
        ),
        encoding="utf-8",
    )
    print(f"[dev-email] Password reset link for {recipient}: {reset_url}")
