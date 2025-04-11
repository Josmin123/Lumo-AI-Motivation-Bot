# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.llms import Ollama
import smtplib
from email.message import EmailMessage

# Load environment
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH", "./data")
MODEL = os.getenv("MODEL", "mistral")
USER_NAME = os.getenv("USER_NAME", "friend")

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

# LLM
llm = Ollama(model=MODEL)

# Helpers
def load_tasks():
    task_path = os.path.join(DATA_PATH, "tasks", "today.json")
    if not os.path.exists(task_path):
        return []
    with open(task_path, encoding="utf-8") as f:
        data = json.load(f)
        return [t["title"] for t in data.get("tasks", []) if not t.get("done", False)]
    
def load_goals():
    goals_path = os.path.join(DATA_PATH, "goals.json")
    if not os.path.exists(goals_path):
        return []
    with open(goals_path, encoding="utf-8") as f:
        return json.load(f)


def generate_motivational_tag(task):
    prompt = f"""You're a personal productivity assistant.

The user's task is: "{task}"

Generate a short motivational message (max 15 words) to inspire them to complete this task today.
Make it modern, encouraging, and punchy."""
    return llm.invoke(prompt)
def match_task(response_task, tasks):
    response_task = response_task.lower().strip().replace("to ", "").rstrip(".")
    for t in tasks:
        if response_task in t.lower().strip():
            return t
    return None


def select_priority_task(tasks):
    goals = load_goals()
    goals_text = ", ".join(goals) if goals else "None provided"

    if len(tasks) == 1:
        return tasks[0], "Only one task today, so that's your focus!"

    prompt = f"""You're a productivity assistant helping your user prioritize their day.

🧠 User's goals: {goals_text}

🎯 Today's tasks:
{chr(10).join([f"{i+1}. {task}" for i, task in enumerate(tasks)])}

Choose the single task the user should focus on FIRST today.

Prefer tasks that clearly align with the user's goals.
Choose the one with the most long-term personal impact.
Ignore "nice-to-have" or low-effort tasks unless no goal-aligned tasks exist.

⚠️ Return ONLY in this format (exactly):
Task: <copy-paste task title>
Reason: <why this matters + which goal it supports>
"""

    response = llm.invoke(prompt).strip()
    print("[Raw response from LLM]:\n", response)


    lines = [line.strip() for line in response.splitlines()]
    task_line = next((line for line in lines if line.lower().startswith("task:")), "")
    reason_line = next((line for line in lines if line.lower().startswith("reason:")), "")

    task = task_line.replace("Task:", "").strip()
    reason = reason_line.replace("Reason:", "").strip()

    matched_task = match_task(task, tasks)
    if matched_task:
        return matched_task, reason or "Because it supports one of your main goals."
    else:
        return tasks[0], "Fallback to first task (response was not recognized)."

def generate_message(task):
    tag = generate_motivational_tag(task)
    return (
        f"🌞Hey, {USER_NAME}!\n\n"
        f"Today's highlight task:\n👉 {task}\n\n"
        f"💬 Motivation boost:\n{tag.strip()}\n\n"
        f"🧠 Lumo tip: You’ve got this. One step at a time.\n"
    )

def log_message(message):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("logs/motivation_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{'-'*50}\n{timestamp} - Daily Motivation:\n{message}\n")
    except PermissionError:
        pass

def send_email(subject, content):
    if not all([SENDER_EMAIL, RECEIVER_EMAIL, EMAIL_PASSWORD]):
        print("Missing email config in .env")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(content)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f" Failed to send email: {e}")

# Main
if __name__ == "__main__":
    print("Generating daily motivation...")

    tasks = load_tasks()
    if not tasks:
        goals = load_goals()
        prompt = f"""The user has not entered any tasks for today.

    Here are their personal goals: {', '.join(goals)}

    Suggest ONE task they can do today that aligns best with one of these goals.

    Return only the task. Make it practical and achievable today.
    """
        suggested_task = llm.invoke(prompt).strip()
        message = (
            f"Hey, {USER_NAME}!\n\n"
            f"You haven’t added any tasks today, but here’s a suggestion:\n"
            f"👉 {suggested_task}\n\n"
            f"Make progress toward your goals — one step at a time!"
        )

        print("🤖 Suggested Task:", suggested_task)
        log_message(message)
        send_email("Your Lumo Motivation for Today", message)
        print("Motivation generated, logged, and emailed.")
        exit()
    else:
        priority_task, reason = select_priority_task(tasks)
        message = generate_message(priority_task)
        message += f"\n🔎 Why this task?\n{reason}"
        print(f"Prioritized Task: {priority_task}")
        print(f"Reason: {reason}")

    log_message(message)
    send_email("Your Lumo Motivation for Today", message)
    print("Motivation generated, logged, and emailed.")
