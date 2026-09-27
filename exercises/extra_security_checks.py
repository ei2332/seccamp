"""選択課題の修正条件。指定したときだけ実行する。"""

pytest_plugins = ["tests.conftest"]


def test_print_heading_is_text(client):
    response = client.get("/trips/1/print", query_string={"heading": "<b>見出し確認</b>"})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<b>見出し確認</b>" not in html
    assert "&lt;b&gt;見出し確認&lt;/b&gt;" in html


def test_guide_download_stays_in_directory(app, client, tmp_path):
    guides = tmp_path / "guides"
    guides.mkdir()
    (tmp_path / "private-note.txt").write_text("検証専用の非公開メモ", encoding="utf-8")
    app.config["TRAVEL_GUIDE_DIR"] = str(guides)
    response = client.get("/travel-guides/download", query_string={"name": "../private-note.txt"})
    assert response.status_code in (400, 404)
    assert "検証専用の非公開メモ" not in response.get_data(as_text=True)
