import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def send_email_with_csv(recipient_email):
    sender_email = "mares90@naver.com"
    sender_password = "coramdeo2016!"
    subject = "CSV File Backup"
    body = "Please find the attached CSV backup file."

    # 이메일 메시지 생성
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # CSV 파일 첨부
    filename = "reservations.csv"
    attachment = open(filename, "rb")

    part = MIMEBase("application", "octet-stream")
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename= " + filename)

    msg.attach(part)

    # SMTP 서버 설정 및 이메일 전송
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, recipient_email, text)
    server.quit()

    print(f"Email sent to {recipient_email} with the CSV backup.")
