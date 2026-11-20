import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server("127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1]
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        return response.status, response.getheaders(), response.read().decode("utf-8")

    def test_home_page_contains_url_form(self):
        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('action="/shorten"', body)
        self.assertIn('name="url"', body)

    def test_shorten_form_returns_escaped_result_and_redirects(self):
        url = "https://example.com/?q=<tag>"
        status, _, body = self.request(
            "POST",
            "/shorten",
            urlencode({"url": url}),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 200)
        self.assertIn("&lt;tag&gt;", body)
        self.assertNotIn("<tag>", body)
        self.assertIn('href="/r/1"', body)

        status, headers, _ = self.request("GET", "/r/1")
        self.assertEqual(status, 302)
        self.assertIn(("Location", url), headers)

    def test_invalid_url_and_unknown_code_return_client_errors(self):
        status, _, _ = self.request(
            "POST",
            "/shorten",
            urlencode({"url": "ftp://example.com"}),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)
        status, _, _ = self.request("GET", "/r/missing")
        self.assertEqual(status, 404)

    def test_table_page_shows_hash_trace_and_probe_count(self):
        self.request(
            "POST",
            "/shorten",
            urlencode({"url": "https://example.com/"}),
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        status, _, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("Horner", body)
        self.assertIn("검사", body)
        self.assertIn("https://example.com/", body)


if __name__ == "__main__":
    unittest.main()
