"""印刷表示と旅行資料の通常動作。"""

import pytest


def test_print_heading_and_trip_body(client):
    response = client.get("/trips/1/print", query_string={"heading": "週末の散歩"})
    assert response.status_code == 200
    assert "<h1>週末の散歩</h1>" in response.get_data(as_text=True)
    assert "公開の本文" in response.get_data(as_text=True)


def test_print_default_heading(client):
    response = client.get("/trips/1/print")
    assert "公開の散歩プラン" in response.get_data(as_text=True)


@pytest.mark.parametrize("user_id,trip_id,status", [(0, 5, 404), (0, 6, 404), (2, 5, 200), (2, 6, 404), (1, 6, 200)])
def test_print_respects_trip_visibility(client, login, user_id, trip_id, status):
    login(user_id)
    response = client.get(f"/trips/{trip_id}/print")
    assert response.status_code == status


def test_download_guide_from_fixture(app, client, tmp_path):
    guides = tmp_path / "guides"
    guides.mkdir()
    (guides / "packing-list.txt").write_text("テスト用の持ち物一覧", encoding="utf-8")
    app.config["TRAVEL_GUIDE_DIR"] = str(guides)
    response = client.get("/travel-guides/download", query_string={"name": "packing-list.txt"})
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "テスト用の持ち物一覧"
    assert response.mimetype == "text/plain"
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert client.get("/travel-guides/download?name=missing.txt").status_code == 404
