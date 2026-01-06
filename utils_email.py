# utils_email.py
import smtplib
from email.mime.text import MIMEText
from config import Config

def send_booking_confirm_email(to_email, hall_name, hall_address, from_date, to_date, total_price):
    subject = "Your hall booking is confirmed - EventHub"
    maps_link = f"https://www.google.com/maps/search/?api=1&query={hall_address.replace(' ', '+')}"
    body = (
        f"Dear Organizer,\n\n"
        f"Your booking has been APPROVED!\n\n"
        f"Hall: {hall_name}\n"
        f"Address: {hall_address}\n"
        f"Google Maps: {maps_link}\n"
        f"Dates: {from_date} to {to_date}\n"
        f"Total Price: ₹{total_price}\n\n"
        f"Regards,\n"
        f"EventHub Team"
    )
    # keep the rest of your function exactly same (MIMEText, SMTP, etc.)


    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to_email

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        if Config.SMTP_TLS:
            server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)


def send_booking_confirm_email_with_food(to_email, hall_name, hall_location, from_date, to_date, hall_price, food_details, total_amount, booking_id):
    subject = "Your booking is confirmed - Payment Required - EventHub"
    body = (
        f"Dear Organizer,\n\n"
        f"✅ Your booking has been APPROVED!\n\n"
        f"🏛️ Hall: {hall_name}\n"
        f"📍 Location: {hall_location}\n"
        f"📆 Dates: {from_date} to {to_date}\n"
        f"💰 Hall Price: ₹{hall_price}\n"
        f"{food_details}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 TOTAL AMOUNT: ₹{total_amount}\n\n"
        f"Complete your payment here:\n"
        f"http://127.0.0.1:5000/organizer/payment/{booking_id}\n\n"
        f"Payment Options:\n"
        f"• UPI: eventhub@upi\n"
        f"• Card: Pay at venue counter\n"
        f"• Cash: Accepted at venue\n\n"
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
