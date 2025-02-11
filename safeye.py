import os
import csv
import json
import requests
import smtplib
import threading
import logging
from email.message import EmailMessage
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv  # Import load_dotenv function

# Load environment variables from .env file
load_dotenv()

# Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "user@example.com")
SMTP_PASS = os.getenv("SMTP_PASS", "password")
SMTP_FROM = os.getenv("SMTP_FROM", "sender@example.com")

LOGS_DIR = "logs"
RESUME_LOG_FILE = "resume.log"
REQUESTS_CSV = "requests.csv"

CHECK_INTERVAL = 30 * 60  # 30 minutes


def send_email(to_emails, subject, body):
    """
    Sends an email to the specified recipients with the given subject and body.

    Parameters:
        to_emails (list): A list of email addresses to send the email to.
        subject (str): The subject of the email.
        body (str): The content of the email.

    Returns:
        None
    """
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            print(f"Email sent to {', '.join(to_emails)}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def read_requests_csv(file_path):
    """
    Reads a CSV file containing request configurations and returns a list of dictionaries.

    Each dictionary represents a request configuration with the following keys:
    - client: The client name
    - project_name: The project name
    - endpoint: The request endpoint
    - expected_http_status: The expected HTTP status code
    - notify_emails: A list of email addresses to notify
    - body: The request body
    - headers: The request headers
    - http_method: The HTTP method (e.g., GET, POST, PUT, DELETE)

    Parameters:
    file_path (str): The path to the CSV file containing request configurations

    Returns:
    list: A list of dictionaries representing the request configurations
    """
    request_configs = []
    with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            try:
                headers = (
                    json.loads(row.get("headers_json", "{}"))
                    if row.get("headers_json")
                    else {}
                )
            except json.JSONDecodeError:
                print(f"Invalid headers_json in row: {row}")
                headers = {}

            try:
                body = (
                    json.loads(row.get("body_json", ""))
                    if row.get("body_json")
                    else None
                )
            except json.JSONDecodeError:
                print(f"Invalid body_json in row: {row}")
                body = None

            emails = [
                email.strip()
                for email in row.get("notify_emails", "").split(",")
                if email.strip()
            ]
            expected_status = int(row.get("expected_http_status", 200))
            http_method = row.get("http_method", "GET").upper()
            project_name = row.get("project_name", "default_project")
            client = row.get("client", "")

            config = {
                "client": client,
                "project_name": project_name,
                "endpoint": row.get("endpoint"),
                "expected_http_status": expected_status,
                "notify_emails": emails,
                "body": body,
                "headers": headers,
                "http_method": http_method,
            }
            request_configs.append(config)
    return request_configs


def ensure_log_dir():
    """
    Ensures the existence of the log directory.

    If the log directory does not exist, it is created.

    Parameters:
        None

    Returns:
        None
    """

    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)


def sanitize_filename(name):
    """
    Sanitizes a filename by replacing non-alphanumeric characters with underscores.

    Parameters:
        name (str): The filename to be sanitized.

    Returns:
        str: The sanitized filename.
    """
    return "".join(c if c.isalnum() else "_" for c in name)


def clean_old_logs(log_dir, max_age_days=30):
    """
    Deletes old log files from the specified directory.

    Parameters:
        log_dir (str): The directory containing log files to be cleaned.
        max_age_days (int): The maximum age of log files in days. Default is 30.

    Returns:
        None
    """
    now = datetime.now()
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            if (now - file_modified) > timedelta(days=max_age_days):
                os.remove(file_path)
                print(f"Deleted old log file: {file_path}")


def execute_requests():
    """
    Executes a series of HTTP requests based on configurations read from a CSV file.

    The function reads request configurations from the REQUESTS_CSV file, sets up logging for each project,
    and sends HTTP requests according to the configurations. It also checks the response status code and
    sends email notifications if the status code is unexpected or if an error occurs during the request.

    The function returns None.
    """
    print(f"Executing requests at {datetime.now().isoformat()}")
    ensure_log_dir()
    clean_old_logs(LOGS_DIR)

    request_configs = read_requests_csv(REQUESTS_CSV)
    total_projects = len(request_configs)
    projects_in_alert = 0

    for config in request_configs:
        project_log_filename = f"{sanitize_filename(config['project_name'])}.log"
        project_log_path = os.path.join(LOGS_DIR, project_log_filename)

        logger = logging.getLogger(config["project_name"])
        logger.setLevel(logging.INFO)
        # Remove previous handlers
        if logger.hasHandlers():
            logger.handlers.clear()
        handler = logging.FileHandler(project_log_path)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(
            f"Starting request for {config['client']} - {config['project_name']}"
        )

        try:
            response = requests.request(
                method=config["http_method"],
                url=config["endpoint"],
                headers=config["headers"],
                json=config["body"],
                timeout=10,
            )
            status_code = response.status_code
            logger.info(
                f"Request to {config['endpoint']} completed with status {status_code}"
            )

            if status_code != config["expected_http_status"]:
                error_msg = (
                    f"Unexpected status code: Expected {config['expected_http_status']}, "
                    f"got {status_code}"
                )
                logger.error(error_msg)
                projects_in_alert += 1
                if config["notify_emails"]:
                    send_email(
                        to_emails=config["notify_emails"],
                        subject=f"Unexpected status code from {config['endpoint']}",
                        body=error_msg,
                    )
        except Exception as e:
            error_msg = f"Error during request to {config['endpoint']}: {e}"
            logger.error(error_msg)
            projects_in_alert += 1
            if config["notify_emails"]:
                send_email(
                    to_emails=config["notify_emails"],
                    subject=f"Error during request to {config['endpoint']}",
                    body=error_msg,
                )
        finally:
            logger.info(
                f"Finished request for {config['client']} - {config['project_name']}"
            )

    # Write summary to resume log
    summary = f"{datetime.now().isoformat()} | {total_projects} analysed projects | {projects_in_alert} projects in alert\n"
    with open(RESUME_LOG_FILE, "a") as resume_log:
        resume_log.write(summary)
    print(summary)


def scheduler():
    """
    Executes the `execute_requests` function and schedules a new timer to call `scheduler` again after the specified interval.

    This function is used to create a recurring task that periodically executes the `execute_requests` function. It starts by calling `execute_requests` immediately and then schedules a new timer using `threading.Timer` to call `scheduler` again after the specified interval.

    Parameters:
    None

    Returns:
    None
    """
    execute_requests()
    threading.Timer(CHECK_INTERVAL, scheduler).start()


if __name__ == "__main__":
    scheduler()
