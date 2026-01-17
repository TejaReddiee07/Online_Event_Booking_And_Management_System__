import smtplib
from email.mime.text import MIMEText
from config import Config



def _send_raw_email(to_email: str, subject: str, body: str):
    """Low-level email sender with proper TLS and error handling."""
    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_FROM
    msg["To"] = to_email

    # Guard against missing credentials
    if not Config.SMTP_USER or not Config.SMTP_PASSWORD:
        raise RuntimeError("SMTP credentials not configured")

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as server:
        if Config.SMTP_TLS:
            server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)



# ---------------- APPROVAL EMAILS ---------------- #



def send_booking_confirm_email(
    to_email,
    hall_name,
    hall_address,
    from_date,
    to_date,
    total_price,
):
    subject = "Your hall booking is confirmed - EventHub"
    maps_link = (
        f"https://www.google.com/maps/search/?api=1&query="
        f"{hall_address.replace(' ', '+')}"
    )
    body = (
        "Dear User,\n\n"
        "Your booking has been APPROVED!\n\n"
        f"Hall: {hall_name}\n"
        f"Address: {hall_address}\n"
        f"Google Maps: {maps_link}\n"
        f"Dates: {from_date} to {to_date}\n"
        f"Total Price: ₹{total_price}\n\n"
        "💳 For Payment, please contact:\n"
        "📧 Email: nagatejareddygoli@gmail.com\n"
        "📞 Phone: 7994693055\n\n"
        "Regards,\n"
        "EventHub Team"
    )
    _send_raw_email(to_email, subject, body)



def send_booking_confirm_email_with_food(
    to_email,
    hall_name,
    hall_location,
    from_date,
    to_date,
    hall_price,
    food_details,
    total_amount,
    booking_id,
    base_url="https://online-event-booking-8.onrender.com",
):
    subject = "Your booking is confirmed - EventHub"

    body = (
        "Dear User,\n\n"
        "✅ Your booking has been APPROVED!\n\n"
        f"🏛️ Hall: {hall_name}\n"
        f"📍 Location: {hall_location}\n"
        f"📆 Dates: {from_date} to {to_date}\n"
        f"💰 Hall Price: ₹{hall_price}\n"
        f"{food_details}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 TOTAL AMOUNT: ₹{total_amount}\n\n"
        "👇 For completing the payment, please contact:\n"
        "📧 **Email**: nagatejareddygoli@gmail.com\n"
        "📞 **Phone**: 7994693055\n\n"
        "Thank you for using EventHub!\n"
        "Team EventHub"
    )

    _send_raw_email(to_email, subject, body)



# ---------------- REJECTION EMAILS ---------------- #



def send_booking_rejected_email(
    to_email,
    hall_name,
    from_date,
    to_date,
    reason: str | None = None,
):
    """Hall / hall+food booking rejected."""
    subject = "Your booking has been rejected - EventHub"

    reason_text = f"Reason: {reason}\n\n" if reason else ""
    body = (
        "Dear User,\n\n"
        "Your booking has been REJECTED by the admin.\n\n"
        f"Hall: {hall_name}\n"
        f"Dates: {from_date} to {to_date}\n"
        f"{reason_text}"
        "If you have any questions, please contact support or try booking another slot.\n\n"
        "Regards,\n"
        "EventHub Team"
    )
    _send_raw_email(to_email, subject, body)



def send_food_booking_rejected_email(
    to_email,
    package_name,
    event_date,
    reason: str | None = None,
):
    """Food‑only booking rejected."""
    subject = "Your food booking has been rejected - EventHub"

    reason_text = f"Reason: {reason}\n\n" if reason else ""
    body = (
        "Dear User,\n\n"
        "Your food booking has been REJECTED by the admin.\n\n"
        f"Food Package: {package_name}\n"
        f"Event Date: {event_date}\n"
        f"{reason_text}"
        "You can try booking another package or contact support for details.\n\n"
        "Regards,\n"
        "EventHub Team"
    )
    _send_raw_email(to_email, subject, body)



def send_booking_auto_rejected_unavailable_email(
    to_email,
    hall_name,
    from_date,
    to_date,
):
    """Auto-reject when same hall & same dates already booked."""
    subject = "Hall not available for selected dates - EventHub"

    body = (
        "Dear User,\n\n"
        "Your booking request has been REJECTED automatically because the hall "
        "is already booked for the selected date(s).\n\n"
        f"Hall: {hall_name}\n"
        f"Dates: {from_date} to {to_date}\n"
        "Reason: The hall is not available on these dates as another booking already exists.\n\n"
        "Please try different dates or another hall.\n\n"
        "Regards,\n"
        "EventHub Team"
    )

    _send_raw_email(to_email, subject, body)



# ---------------- ADMIN NOTIFY EMAIL ---------------- #



def send_admin_new_booking_email(
    to_email,
    organizer_name,
    booking_kind,   # "Hall" or "Food"
    hall_or_package,
    from_date,
    to_date,
    extra_info="",
):
    """Notify admin when a new booking is created."""
    subject = f"New {booking_kind} booking request - EventHub"

    body = (
        "Dear Admin,\n\n"
        f"A new {booking_kind.upper()} booking has been created.\n\n"
        f"User: {organizer_name}\n"
        f"{'Hall' if booking_kind == 'Hall' else 'Food Package'}: {hall_or_package}\n"
        f"From: {from_date}\n"
        f"To: {to_date}\n"
        f"{extra_info}\n"
        "Please review this booking in the admin panel and approve or reject it.\n\n"
        "Regards,\n"
        "EventHub System"
    )

    _send_raw_email(to_email, subject, body)
