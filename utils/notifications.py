
"""
Notification Manager for Market-Rover.
Handles sending alerts and reports via Email (SMTP).
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class EmailManager:
    """
    Manages email notifications using SMTP.
    Requires [email] section in .streamlit/secrets.toml
    """
    def __init__(self):
        self._config = self._load_config()
        
    def _load_config(self):
        """Load email config from secrets."""
        try:
            return st.secrets.get("email", {})
        except FileNotFoundError:
            logger.warning("Secrets file not found. Email disabled.")
            return {}

    def is_configured(self):
        """Check if email is configured."""
        required_keys = ["smtp_server", "smtp_port", "sender_email", "sender_password", "recipient_email"]
        return all(key in self._config for key in required_keys)

    def send_email(self, subject, body, to_email=None, is_html=False):
        """
        Send an email via SMTP.
        
        Args:
            subject (str): Email subject.
            body (str): Email body content.
            to_email (str, optional): Recipient email. Defaults to secrets config.
            is_html (bool): True if body is HTML, False for plain text.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_configured():
            logger.warning("Email not configured. Skipping.")
            return False
            
        recipient = to_email or self._config.get("recipient_email")
        if not recipient:
            logger.error("No recipient email specified.")
            return False

        msg = MIMEMultipart()
        msg['From'] = self._config.get("sender_email")
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        try:
            server = smtplib.SMTP(self._config.get("smtp_server"), self._config.get("smtp_port"))
            server.starttls()
            server.login(self._config.get("sender_email"), self._config.get("sender_password"))
            text = msg.as_string()
            server.sendmail(self._config.get("sender_email"), recipient, text)
            server.quit()
            logger.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
