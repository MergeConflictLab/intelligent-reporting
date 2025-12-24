import smtplib
import os
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class EmailSender:
    def __init__(self):
        self._sender_email = "amineachouhame51@gmail.com"
        self._app_password = "qlamguapgpsmscrk"
    def _send_email_with_attachments(self, sender_email, app_password, receiver_email, subject, body, folder_path):
        # Create the email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        # Add email body
        msg.attach(MIMEText(body, "plain"))

        # Loop all files in folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if os.path.isfile(file_path):
                # Guess file type
                content_type, encoding = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = "application/octet-stream"

                main_type, sub_type = content_type.split("/", 1)

                # Open file
                with open(file_path, "rb") as f:
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(f.read())

                # Encode the file
                encoders.encode_base64(part)

                # Add header
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}"
                )

                # Attach to message
                msg.attach(part)

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        print("Email sent with attachments!")
    def send_email(self, receiver_email, subject, body, folder_path):
        self._send_email_with_attachments(
            sender_email=self._sender_email,
            app_password=self._app_password,
            receiver_email=receiver_email,
            subject=subject,
            body=body,
            folder_path=folder_path
        )
