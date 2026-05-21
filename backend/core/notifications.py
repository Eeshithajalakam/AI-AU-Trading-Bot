import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.parse
import json
import threading
from core.config import settings

class NotificationManager:
    def __init__(self):
        pass

    def send_alert(self, title: str, message: str, level: str = "INFO"):
        """
        Sends an alert to all configured channels (Telegram, Email).
        Uses background threads to avoid blocking the main trading loop.
        """
        formatted_msg = f"[{level}] {title}\n\n{message}"
        print(f"🔔 NOTIFICATION: {formatted_msg}")
        
        threading.Thread(target=self._send_telegram_sync, args=(formatted_msg,)).start()
        threading.Thread(target=self._send_email_sync, args=(title, formatted_msg)).start()

    def _send_telegram_sync(self, text: str):
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            return
            
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"Telegram alert failed: {e}")

    def _send_email_sync(self, subject: str, text: str):
        if not settings.SMTP_SERVER or not settings.SMTP_USER or not settings.NOTIFICATION_EMAIL:
            return
            
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.NOTIFICATION_EMAIL
        msg['Subject'] = f"AuTrade AI: {subject}"
        msg.attach(MIMEText(text, 'plain'))
        
        try:
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Email alert failed: {e}")

# Global singleton
notifier = NotificationManager()
