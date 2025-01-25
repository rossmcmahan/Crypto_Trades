from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

#Email configuration
load_dotenv()
SENDER_EMAIL = "rossmcmahanalerts@gmail.com"
APP_PASSWORD = "avcsqpimcnhqwnex"
RECIPIENT_EMAIL = "rossmcmahan@gmail.com"

def send_email_notifications(file_path):
	subject = "Last 24 hrs of BTC Trades"
	body = "Attached are the BTC Trades from the last 24 hours... \n\n"

	msg = MIMEMultipart()
	msg['From'] = SENDER_EMAIL
	msg['To'] = RECIPIENT_EMAIL
	msg['Subject'] = subject
	msg.attach(MIMEText(body, 'plain'))

	try:
		with open(file_path, "rb") as attachment:
			part = MIMEBase("application", "octet-stream")
			part.set_payload(attachment.read())
		encoders.encode_base64(part)
		part.add_header(
			"Content-Disposition",
			f"attachment; filename = {file_path.split('/')[-1]}",
		)
		msg.attach(part)

	except FileNotFoundError:
		print(f"File {file_path} not found. Email will be sent without the attachment.")


	try:
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(SENDER_EMAIL, APP_PASSWORD)
		text = msg.as_string()
		server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, text)
		server.quit()

	except Exception as e:
		print(f"Failed to send email notification { e }")
