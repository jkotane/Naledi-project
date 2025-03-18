import smtplib

sender = "jacky.kotane@afrinnovae.com"
receiver = "jacky@nnovaex.com"
password = "bqmu tsje tmpu dqbm"

message = """Subject: Test Email
This is a test email sent from Python."""

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, message)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")