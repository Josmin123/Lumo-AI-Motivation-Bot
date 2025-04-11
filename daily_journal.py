import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
from dotenv import load_dotenv
from langchain_community.llms import Ollama

load_dotenv()

# Environment Variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")
MODEL = os.getenv("MODEL", "mistral")
DATA_PATH = os.getenv("DATA_PATH", "./data")
JOURNAL_PATH = os.path.join(DATA_PATH, "journal")

# Ensure journal folder exists
os.makedirs(JOURNAL_PATH, exist_ok=True)

def send_journal_prompt():
    subject = "📝 Your MeOS End-of-Day Reflection"
    body = """
Hi there,

How did your day go? Reply to this email with your reflections:

1. How did your day go overall?
2. What are you most proud of today?
3. What drained your energy today?

I'll reflect on it and send you some motivation 🌟

- MeOS
    """
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        print("✅ Journal prompt email sent.")

def fetch_latest_journal_reply():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(SENDER_EMAIL, APP_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, '(UNSEEN FROM "{}")'.format(RECEIVER_EMAIL))
    ids = data[0].split()
    if not ids:
        print("📭 No journal replies found.")
        return None

    latest_id = ids[-1]
    result, data = mail.fetch(latest_id, "(RFC822)")
    raw_email = data[0][1]
    email_msg = email.message_from_bytes(raw_email)

    for part in email_msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode()
            mail.store(latest_id, '+FLAGS', '\\Seen')
            return body.strip()

    return None

def save_journal(content: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(JOURNAL_PATH, f"{date_str}.json")
    with open(filename, "w") as f:
        json.dump({"entry": content, "timestamp": str(datetime.now())}, f, indent=2)
    print(f"✅ Journal saved to {filename}")
    return filename

def summarize_journal(content):
    llm = Ollama(model=MODEL)
    prompt = f"""
You're MeOS, a warm and emotionally intelligent AI reflection coach.

The user just finished their day and shared this journal entry:
\"\"\"{content}\"\"\"

Please do the following:
Start with "Hey there," and then:
1. Respond in a warm, encouraging, and conversational tone — like a supportive friend.
2. Acknowledge the user's efforts and feelings.
3. Gently point out any distractions or stress patterns — with kindness.
4. Suggest one simple way to improve tomorrow — keep it friendly, not preachy.
5. End with an uplifting message or quote that fits their energy today.

Keep your message short and impactful — no more than 5-6 lines. Avoid numbering or sounding like a list. Just make it feel personal, warm, and real.
"""

    return llm.invoke(prompt)

def send_motivation_email(response):
    subject = "🌟 MeOS Reflection for Your Day"
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(response, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        print("✅ Reflection email sent.")

def run_daily_journal():
    print("Sending daily prompt...")
    send_journal_prompt()

    print("\nWaiting for response (manual for now)...")
    input("Press Enter once you've replied to the journal prompt via email...\n")

    content = fetch_latest_journal_reply()
    if content:
        save_journal(content)
        summary = summarize_journal(content)
        print("\n🤖 MeOS Reflection:\n")
        print(summary)
        send_motivation_email(summary)
    else:
        print("❌ No reply found.")

if __name__ == "__main__":
    run_daily_journal()
