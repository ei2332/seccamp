"""公開プラン検索の入力と検索結果に関するテスト。"""

from html.parser import HTMLParser

import pytest

class TripIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.ids.append(int(dict(attrs)["data-trip-id"]))


@pytest.mark.parametrize(
    "query, expected_ids",
    [
        pytest.param("", [1, 2, 3, 4], id="empty-shows-public-only"),
        pytest.param("公開の散歩", [1], id="normal-search"),
        pytest.param("読書プラン", [2], id="japanese-substring"),
        pytest.param("no-such-note", [], id="no-match"),
        pytest.param("限定", [], id="restricted-plans-are-hidden"),
        pytest.param("100%_", [4], id="literal-wildcards"),
        pytest.param("\\", [], id="literal-backslash"),
        pytest.param("O'Reilly", [2], id="legitimate-apostrophe"),
        pytest.param("' OR 1=1 -- ", [], id="sql-input-must-not-reveal-restricted-plans"),
    ],
)
def test_search_contract(app, client, query, expected_ids):
    response = client.get("/", query_string={"q": query})
    assert response.status_code == 200
    parsed = TripIds()
    parsed.feed(response.get_data(as_text=True))
    assert parsed.ids == expected_ids


def test_query_is_displayed_as_text(client):
    response = client.get("/", query_string={"q": '<script>alert("demo")</script>'})
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
