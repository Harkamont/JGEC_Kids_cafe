import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def send_email_with_csv(recipient_email, csv_filename="reservations.csv"):
    # Email configuration
    sender_email = os.environ.get("SENDER_EMAIL", "mares90@naver.com")
    sender_password = os.environ.get("SENDER_PASSWORD", "NFG7M8G6JU7W")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.naver.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    subject = "CSV File Backup"
    body = "Please find the attached CSV backup file."

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach CSV file
    try:
        with open(csv_filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename= {csv_filename}"
            )
            msg.attach(part)
    except FileNotFoundError:
        print(f"Error: The file {csv_filename} was not found.")
        return
    except IOError as e:
        print(f"Error reading the file: {e}")
        return

    # Send email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent to {recipient_email} with the CSV backup.")
    except smtplib.SMTPAuthenticationError:
        print(
            "SMTP Authentication Error: The server didn't accept the username/password combination."
        )
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred while sending the email: {e}")


if __name__ == "__main__":
    recipient = "mares90@naver.com"  # Replace with actual recipient email
    send_email_with_csv(recipient)
