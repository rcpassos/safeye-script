# Safeye - HTTP Endpoint Monitor

A Python script to periodically check HTTP endpoints based on configurations defined in a CSV file. The script logs the results per project, sends email notifications on errors, and includes features like log rotation and unit testing. Ideal for monitoring APIs, websites, and services to ensure they are up and running as expected.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [SMTP Settings](#smtp-settings)
  - [CSV Configuration File](#csv-configuration-file)
- [Usage](#usage)
- [Logging and Monitoring](#logging-and-monitoring)
- [Log Rotation](#log-rotation)
- [Unit Tests](#unit-tests)
- [Contributing](#contributing)
- [License](#license)

## Features

- Reads configurations from a CSV file to perform HTTP requests.
- Supports various HTTP methods (`GET`, `POST`, `PUT`, `DELETE`).
- Allows setting custom headers and body for requests.
- Checks if the response status code matches the expected status.
- Logs the results per project in individual log files.
- Sends email notifications to specified recipients on errors or unexpected status codes.
- Rotates logs by deleting logs older than 30 days.
- Provides unit tests with full coverage using the `unittest` framework.

## Requirements

- Python 3.6 or higher
- Packages:
  - `requests`
  - `unittest` (comes with Python standard library)
  - `python-dotenv`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/rcpassos/safeye-script.git
   cd safeye-script
   ```

2. **Install Dependencies:**

   Install the required Python packages using `pip`:

   ```bash
   pip install requests
   ```

   ```bash
   pip install python-dotenv
   ```

## Configuration

### SMTP Settings

The script requires SMTP settings to send email notifications. You can set these configurations either by setting environment variables or by modifying the script directly.

**Environment Variables:**

Copy the .env.example file to the .env file and replace the dummy values.

```bash
cp .env.example .env
```

**Directly in the Script:**

Open `safeye.py` and modify the SMTP configuration section:

```python
# Configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'your_smtp_host')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', 'your_email@example.com')
SMTP_PASS = os.getenv('SMTP_PASS', 'your_email_password')
SMTP_FROM = os.getenv('SMTP_FROM', 'your_email@example.com')
```

> **Security Note:** If you choose to store your SMTP credentials in the script, ensure that the script is not exposed publicly to avoid compromising your email account.

### Other Configurations

You can change the following directly in the `safeye.py` file.

```python
LOGS_DIR = "logs"
RESUME_LOG_FILE = "resume.log"
REQUESTS_CSV = "requests.csv"
```

CHECK_INTERVAL = 30 \* 60 # 30 minutes

### CSV Configuration File

The script reads configurations from a CSV file named `requests.csv`. This file should be placed in the same directory as the script.

**CSV Format:**

- The CSV file uses semicolons (`;`) as field separators.
- Ensure the file is saved with UTF-8 encoding.

**Columns:**

- `client`: The name of the client or company.
- `project_name`: A descriptive name for the project or check.
- `endpoint`: The URL to which the HTTP request will be made.
- `expected_http_status`: The expected HTTP status code (e.g., `200`).
- `notify_emails`: Comma-separated list of email addresses to notify on errors.
- `body_json`: JSON-formatted string for the request body (if applicable).
- `headers_json`: JSON-formatted string for custom headers.
- `http_method`: HTTP method to use (`GET`, `POST`, `PUT`, `DELETE`).

**Example `requests.csv`:**

```csv
client;project_name;endpoint;expected_http_status;notify_emails;body_json;headers_json;http_method
Acme Corp;Website Uptime Checker;https://example.com/health;200;admin@example.com;;;GET
Beta Inc;API Status Monitor;https://api.example.com/v1/status;200;support@example.com;;{"Authorization": "Bearer YOUR_TOKEN"};GET
Gamma LLC;User Login Test;https://example.com/api/login;200;dev@example.com;{"username": "testuser", "password": "testpass"};{"Content-Type": "application/json"};POST
```

**Notes:**

- For JSON fields (`body_json`, `headers_json`), ensure that the JSON strings are valid.
- If a field is not applicable, leave it empty (e.g., `body_json` for a `GET` request).

## Usage

Run the script using Python:

```bash
python safeye.py
```

The script will:

- Execute immediately upon running.
- Schedule subsequent executions every 30 minutes.

## Logging and Monitoring

- **Per-Project Logs:**

  Logs are saved in the `logs` directory, with each project's logs in a separate file named after the `project_name`.

  ```
  logs/
  ├── project1.log
  ├── project2.log
  └── ...
  ```

- **Summary Log:**

  A summary of each execution is appended to `resume.log` in the script's directory.

  **Example Entry:**

  ```
  2023-10-05T12:00:00.000000 | 5 analysed projects | 2 projects in alert
  ```

## Log Rotation

The script includes a function to clean up old logs:

- Deletes log files in the `logs` directory that are older than 30 days.
- This function runs each time the script executes.

If you prefer to use system tools like `logrotate` on Linux for log management, you can set up a configuration file accordingly.

## Unit Tests

The project includes unit tests with full coverage, located in `test_safeye.py`.

### Running the Unit Tests

1. **Install Coverage Tool (Optional):**

   ```bash
   pip install coverage
   ```

2. **Run Tests Without Coverage:**

   ```bash
   python -m unittest test_safeye.py
   ```

3. **Run Tests With Coverage:**

   ```bash
   coverage run --source=safeye -m unittest test_safeye.py
   coverage report -m
   ```

### Test Coverage Report

The coverage report will display the percentage of code covered by tests and highlight any lines not covered.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Commit Your Changes**

   ```bash
   git commit -am 'Add some feature'
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**

## License

This project is licensed under the [MIT License](LICENSE).

---

**Disclaimer:** Use this script responsibly. Ensure you have permission to perform HTTP requests to the endpoints you configure. The author is not responsible for any misuse of this tool.
