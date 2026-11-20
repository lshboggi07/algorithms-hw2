"""Standard-library HTTP interface for the in-memory URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlsplit

from src.hash_table import HashTable, LinearProbingHashTable
from src.shortener import Shortener


MAX_FORM_BYTES = 65536


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    shortener: Shortener | None = None,
) -> ThreadingHTTPServer:
    application = shortener if shortener is not None else Shortener()

    class ShortenerHandler(BaseHTTPRequestHandler):
        def _send_html(self, status: int, title: str, content: str) -> None:
            page = (
                "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
                f"<title>{html.escape(title)}</title><body>"
                f"<h1>{html.escape(title)}</h1>{content}</body></html>"
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send_html(
                    200,
                    "URL 단축기",
                    '<form action="/shorten" method="post">'
                    '<label>URL <input name="url" type="url" required></label>'
                    '<button type="submit">단축</button></form>'
                    '<p><a href="/table">해시 테이블 보기</a></p>',
                )
                return

            if path == "/table":
                self._send_table()
                return

            if path.startswith("/r/") and path.count("/") == 2:
                code = unquote(path[len("/r/") :])
                try:
                    url = application.expand(code)
                except KeyError:
                    self._send_html(404, "코드를 찾을 수 없습니다", "<p>등록되지 않은 코드입니다.</p>")
                    return
                self.send_response(302)
                self.send_header("Location", url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            self._send_html(
                404, "페이지를 찾을 수 없습니다", "<p>요청한 경로가 없습니다.</p>"
            )

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/shorten":
                self._send_html(
                    404, "페이지를 찾을 수 없습니다", "<p>요청한 경로가 없습니다.</p>"
                )
                return

            try:
                content_length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self._send_html(400, "잘못된 요청", "<p>요청 본문 길이가 잘못되었습니다.</p>")
                return
            if content_length < 0 or content_length > MAX_FORM_BYTES:
                self._send_html(400, "잘못된 요청", "<p>요청 본문이 허용 크기를 벗어났습니다.</p>")
                return

            try:
                form = parse_qs(self.rfile.read(content_length).decode("utf-8"))
            except UnicodeDecodeError:
                self._send_html(400, "잘못된 요청", "<p>폼은 UTF-8이어야 합니다.</p>")
                return
            url = form.get("url", [""])[0]
            try:
                code = application.shorten(url)
            except (TypeError, ValueError) as error:
                self._send_html(
                    400, "잘못된 URL", f"<p>{html.escape(str(error))}</p>"
                )
                return

            escaped_url = html.escape(url)
            escaped_code = html.escape(code)
            short_link = html.escape(f"/r/{quote(code, safe='')}", quote=True)
            self._send_html(
                200,
                "단축 URL 생성 완료",
                f"<p>원본 URL: <code>{escaped_url}</code></p>"
                f'<p>단축 코드: <code>{escaped_code}</code></p>'
                f'<p>단축 링크: <a href="{short_link}">{short_link}</a></p>'
                '<p><a href="/">다른 URL 입력</a></p>',
            )

        def _send_table(self) -> None:
            table = application.table
            rows: list[str] = []
            for index, bucket in enumerate(table.snapshot()):
                nodes: list[str] = []
                for node_index, (key, value) in enumerate(bucket):
                    result = table.probe(key)
                    previous = 0
                    calculation = "h=0"
                    for _, codepoint, accumulator in result.hash_steps:
                        calculation += (
                            f" -> (31*{previous}+{codepoint})%"
                            f"{table.capacity}={accumulator}"
                        )
                        previous = accumulator
                    probe_path = " -> ".join(
                        str(slot) for slot in result.probe_path
                    )
                    code = str(value)
                    short_link = f"/r/{quote(code, safe='')}"
                    nodes.append(
                        '<article class="chain-node">'
                        f"<p><strong>URL 키:</strong> "
                        f"<code>{html.escape(key)}</code></p>"
                        f"<p><strong>짧은 코드:</strong> "
                        f"<code>{html.escape(code)}</code></p>"
                        f'<p><strong>짧은 링크:</strong> '
                        f'<a href="{html.escape(short_link, quote=True)}">'
                        f"{html.escape(short_link)}</a></p>"
                        "<details>"
                        "<summary>Horner 해시 계산 과정</summary>"
                        f"<code>{html.escape(calculation)}</code>"
                        "</details>"
                        f"<p>검사한 슬롯: {html.escape(probe_path)}</p>"
                        f"<p>노드 검사 횟수: {result.probes}</p>"
                        "</article>"
                    )
                    if node_index < len(bucket) - 1:
                        nodes.append('<span class="chain-arrow">→</span>')
                chain = (
                    '<div class="chain">'
                    + "".join(nodes)
                    + '<span class="chain-end">끝</span></div>'
                    if bucket
                    else '<span class="empty-bucket">비어 있음</span>'
                )
                rows.append(
                    f'<tr><th scope="row">{index}</th><td>{chain}</td></tr>'
                )

            content = (
                f"<p>전략: {html.escape(table.strategy)}, 용량: {table.capacity}, "
                f"URL 항목: {len(table)}</p>"
                "<style>"
                ".chain{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}"
                ".chain-node{border:1px solid #888;border-radius:.4rem;"
                "padding:.5rem;max-width:36rem}"
                ".chain-node p{margin:.25rem 0;overflow-wrap:anywhere}"
                ".chain-arrow{font-size:1.5rem;font-weight:bold}"
                ".chain-end,.empty-bucket{color:#555}"
                "table{border-collapse:collapse}th,td{border:1px solid #888;"
                "padding:.5rem;vertical-align:top}"
                "</style>"
                "<table><caption>해시 버킷과 연결 리스트</caption>"
                "<thead><tr><th>버킷</th><th>연결 리스트 노드</th>"
                "</tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table><p><a href=\"/\">돌아가기</a></p>"
            )
            self._send_html(200, "해시 테이블", content)

    return ThreadingHTTPServer((host, port), ShortenerHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--table", choices=("chaining", "linear"), default="chaining"
    )
    args = parser.parse_args()

    table_class = (
        LinearProbingHashTable if args.table == "linear" else HashTable
    )
    server = create_server(
        args.host, args.port, Shortener(table_class=table_class)
    )
    print(f"Serving on http://{args.host}:{args.port}")
    with server:
        server.serve_forever()


if __name__ == "__main__":
    main()
