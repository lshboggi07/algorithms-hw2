import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.hash_table import LinearProbingHashTable
from src.shortener import Shortener
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
        self.assertIn('<a href="/r/1">/r/1</a>', body)

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

    def test_table_page_shows_chains_links_and_collapsible_hash_steps(self):
        server = create_server("127.0.0.1", 0, Shortener(capacity=1))
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1]
        )
        try:
            for url in ("https://example.com/one", "https://example.com/two"):
                connection.request(
                    "POST",
                    "/shorten",
                    urlencode({"url": url}),
                    {"Content-Type": "application/x-www-form-urlencoded"},
                )
                response = connection.getresponse()
                response.read()

            connection.request("GET", "/table")
            response = connection.getresponse()
            body = response.read().decode("utf-8")
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(response.status, 200)
        self.assertIn("https://example.com/one", body)
        self.assertIn("https://example.com/two", body)
        self.assertIn("→", body)
        self.assertIn('<a href="/r/1">/r/1</a>', body)
        self.assertIn('<a href="/r/2">/r/2</a>', body)
        self.assertIn("<details>", body)
        self.assertIn("</details>", body)
        self.assertIn("Horner 해시 계산 과정", body)
        self.assertIn("노드 검사 횟수", body)

    def test_linear_table_page_shows_strategy_and_slots_examined(self):
        server = create_server(
            "127.0.0.1",
            0,
            Shortener(table_class=LinearProbingHashTable, capacity=5),
        )
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1]
        )
        try:
            connection.request(
                "POST",
                "/shorten",
                urlencode({"url": "https://example.com/"}),
                {"Content-Type": "application/x-www-form-urlencoded"},
            )
            response = connection.getresponse()
            response.read()
            connection.request("GET", "/table")
            response = connection.getresponse()
            body = response.read().decode("utf-8")
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertIn("linear probing", body)
        self.assertIn("검사한 슬롯", body)
        self.assertIn("Horner", body)


if __name__ == "__main__":
    unittest.main()
