import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import json
import os
from datetime import datetime, timedelta
from safeye import (
    send_email,
    read_requests_csv,
    ensure_log_dir,
    sanitize_filename,
    clean_old_logs,
    execute_requests,
)


class TestSafeye(unittest.TestCase):

    def setUp(self):
        # Set up any necessary test data or configurations
        pass

    def tearDown(self):
        # Clean up after tests if needed
        pass

    @patch("smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        # Test the send_email function
        to_emails = ["test@example.com"]
        subject = "Test Subject"
        body = "Test Body"

        send_email(to_emails, subject, body)

        mock_smtp.assert_called_once_with("smtp.example.com", 587)
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='client;project_name;endpoint;expected_http_status;notify_emails;headers_json;body_json;http_method\nTestClient;TestProject;http://example.com;200;test@example.com;{"Content-Type": "application/json"};{"key": "value"};GET',
    )
    def test_read_requests_csv(self, mock_file):
        result = read_requests_csv("dummy_path")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["client"], "TestClient")
        self.assertEqual(result[0]["project_name"], "TestProject")
        self.assertEqual(result[0]["endpoint"], "http://example.com")
        self.assertEqual(result[0]["expected_http_status"], 200)
        self.assertEqual(result[0]["notify_emails"], ["test@example.com"])
        self.assertEqual(result[0]["headers"], {"Content-Type": "application/json"})
        self.assertEqual(result[0]["body"], {"key": "value"})
        self.assertEqual(result[0]["http_method"], "GET")

    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_ensure_log_dir(self, mock_makedirs, mock_exists):
        mock_exists.return_value = False
        ensure_log_dir()
        mock_makedirs.assert_called_once_with("logs")

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("test file.log"), "test_file_log")
        self.assertEqual(sanitize_filename("test@file.log"), "test_file_log")
        self.assertEqual(sanitize_filename("test123"), "test123")

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.path.getmtime")
    @patch("os.remove")
    def test_clean_old_logs(
        self, mock_remove, mock_getmtime, mock_isfile, mock_listdir
    ):
        mock_listdir.return_value = ["old_log.log", "new_log.log"]
        mock_isfile.return_value = True
        mock_getmtime.side_effect = [
            (datetime.now() - timedelta(days=31)).timestamp(),
            datetime.now().timestamp(),
        ]

        clean_old_logs("dummy_log_dir")

        mock_remove.assert_called_once_with("dummy_log_dir/old_log.log")

    @patch("safeye.read_requests_csv")
    @patch("safeye.requests.request")
    @patch("safeye.send_email")
    @patch("builtins.open", new_callable=mock_open)
    @patch("safeye.datetime")
    def test_execute_requests(
        self, mock_datetime, mock_file, mock_send_email, mock_request, mock_read_csv
    ):
        mock_datetime.now.return_value = datetime(2024, 9, 28, 22, 35, 22, 5085)
        mock_read_csv.return_value = [
            {
                "client": "TestClient",
                "project_name": "TestProject",
                "endpoint": "http://example.com",
                "expected_http_status": 200,
                "notify_emails": ["test@example.com"],
                "headers": {},
                "body": None,
                "http_method": "GET",
            }
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        execute_requests()

        mock_request.assert_called_once_with(
            method="GET", url="http://example.com", headers={}, json=None, timeout=10
        )
        mock_send_email.assert_not_called()

        # Check that write was called 4 times
        self.assertEqual(mock_file().write.call_count, 4)

        # Check the content of the last write call (summary log)
        expected_summary = (
            "2024-09-28T22:35:22.005085 | 1 analysed projects | 0 projects in alert\n"
        )
        mock_file().write.assert_has_calls([call(expected_summary)], any_order=True)


if __name__ == "__main__":
    unittest.main()
