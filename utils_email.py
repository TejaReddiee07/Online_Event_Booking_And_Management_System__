# utils_email.py
import smtplib
from email.mime.text import MIMEText
from config import Config

# Original function (keep for backward compatibility)
def send_booking_confirm_email(to_email, hall_name, from_date, to_date, total_price):
    subject = "Your hall booking is confirmed - EventHub"
    body = (
        f"Dear Organizer,\n\n"
        f"Your booking has been APPROVED!\n\n"
        f"Hall: {hall_name}\n"
        f"Dates: {from_date} to {to_date}\n"
        f"Total Amount: ₹{total_price}\n\n"
        f"Please make payment via UPI or card at the venue.\n\n"
        f"Thank you for using EventHub!\n"
        f"Team EventHub"
    )

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to_email

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        if Config.SMTP_TLS:
            server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)


# New function for hall + food bookings
def send_booking_confirm_email_with_food(to_email, hall_name, from_date, to_date, hall_price, food_details, total_amount):
    subject = "Your booking is confirmed - Payment Required - EventHub"
    body = (
        f"Dear Organizer,\n\n"
        f"✅ Your booking has been APPROVED!\n\n"
        f"📅 Hall: {hall_name}\n"
        f"📆 Dates: {from_date} to {to_date}\n"
        f"💰 Hall Price: ₹{hall_price}\n"
        f"{food_details}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 TOTAL AMOUNT: ₹{total_amount}\n\n"
        f"Payment Options:\n"
        f"• UPI: eventhub@upi (scan QR at venue)\n"
        f"• Card: Pay at venue counter\n"
        f"• Online: Visit eventhub.com/payment\n\n"
        f"You have booked hall and food for your event!\n\n"
        f"Thank you for using EventHub!\n"
        f"Team EventHub"
    )

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to_email

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        if Config.SMTP_TLS:
            server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)
