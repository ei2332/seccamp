"""プランの閲覧・編集と公開範囲に関する回帰テスト。"""

import pytest

from app.database import open_database
from app.main import create_app


@pytest.mark.parametrize("user_id,trip_id,status", [
    (0, 1, 200), (0, 5, 404), (0, 6, 404),
    (1, 5, 200), (1, 6, 200),
    (2, 5, 200), (2, 6, 404),
    (3, 5, 404), (3, 6, 404),
])
def test_visibility(client, login, user_id, trip_id, status):
    login(user_id)
    response = client.get(f"/trips/{trip_id}")
    assert response.status_code == status
    if status == 404:
        assert "グループ専用の本文" not in response.get_data(as_text=True)
        assert "自分専用の本文" not in response.get_data(as_text=True)


@pytest.mark.parametrize("user_id,trip_id", [(0, 1), (2, 1), (2, 5), (3, 6)])
def test_only_owner_can_edit(client, login, post, user_id, trip_id):
    login(user_id)
    assert client.get(f"/trips/{trip_id}/edit").status_code in (403, 404)
    response = post(f"/trips/{trip_id}/edit", {"title": "侵入", "destination": "変更", "body": "変更", "visibility": "public"})
    assert response.status_code in (403, 404)
    login(1)
    assert "侵入" not in client.get(f"/trips/{trip_id}").get_data(as_text=True)


def test_create_default_is_private_and_guest_cannot_create(client, post):
    assert client.get("/trips/new").status_code == 403
    assert post("/trips/new", {}).status_code == 403


@pytest.mark.parametrize("visibility,expected", [("public", [200, 200, 200]), ("friends", [404, 200, 404]), ("private", [404, 404, 404])])
def test_create_persist_and_scope(app, client, login, post, visibility, expected):
    login(1)
    assert 'value="private" checked' in client.get("/trips/new").get_data(as_text=True)
    with open_database(app.config["DATABASE"]) as db:
        before_count = db.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    response = post("/trips/new", {"title": "架空の旅", "destination": "架空の街", "body": "予定\n記録", "visibility": visibility, "group_id": "1", "owner_id": "3"})
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "架空の旅" in client.get(location).get_data(as_text=True)
    for user_id, status in zip([0, 2, 3], expected):
        login(user_id)
        assert client.get(location).status_code == status
    login(1)
    assert client.get(location + "/edit").status_code == 200
    # 作り直したアプリも同じDBの追加データを保持する。
    second = create_app({"TESTING": True, "DATABASE": app.config["DATABASE"]})
    with second.test_client() as second_client:
        assert second_client.get(location).status_code == (200 if visibility == "public" else 404)
    with open_database(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == before_count + 1


def test_scope_changes_revoke_access(app, client, login, post):
    login(1)
    data = {"title": "共有の旅", "destination": "山梨", "body": "集合計画", "visibility": "friends", "group_id": "1"}
    assert post("/trips/5/edit", data).status_code == 302
    login(2)
    assert client.get("/trips/5").status_code == 200
    login(1)
    data["visibility"] = "private"
    assert post("/trips/5/edit", data).status_code == 302
    login(2)
    assert client.get("/trips/5").status_code == 404
    assert "共有の旅" not in client.get("/my-trips").get_data(as_text=True)
    login(1)
    data["visibility"] = "friends"
    assert post("/groups", {"action": "create", "name": "新しい仲間"}).status_code == 302
    with open_database(app.config["DATABASE"]) as db:
        group = db.execute("SELECT * FROM travel_groups WHERE name = ?", ("新しい仲間",)).fetchone()
    login(3)
    assert post("/groups", {"action": "join", "invite_code": group["invite_code"]}).status_code == 302
    login(1)
    data["group_id"] = str(group["id"])
    assert post("/trips/5/edit", data).status_code == 302
    login(2)
    assert client.get("/trips/5").status_code == 404
    login(3)
    assert client.get("/trips/5").status_code == 200


def test_my_page_only_shows_owned_and_invited(client, login):
    login(2)
    html = client.get("/my-trips").get_data(as_text=True)
    assert "グループ限定の散歩プラン" in html
    assert "自分限定の散歩プラン" not in html
    login(3)
    assert "グループ限定の散歩プラン" not in client.get("/my-trips").get_data(as_text=True)


@pytest.mark.parametrize("field,value", [("title", ""), ("title", "a" * 101), ("destination", ""), ("body", "a" * 4001), ("visibility", "invalid"), ("members", "999"), ("members", "2 OR 1=1")])
def test_form_validation(login, post, field, value):
    login(1)
    data = {"title": "旅", "destination": "街", "body": "予定", "visibility": "friends", "group_id": "1"}
    assert post("/trips/new", data).status_code == 302
    data[field] = value
    assert post("/trips/new", data).status_code == 400


@pytest.mark.parametrize("path", ["/demo-user", "/trips/new", "/trips/1/edit"])
def test_posts_require_csrf(client, login, path):
    login(1)
    assert client.post(path, data={"user_id": "2"}).status_code == 400
    assert client.post(path, data={"csrf_token": "wrong"}).status_code == 400


def test_content_is_escaped(client, login, post):
    login(1)
    response = post("/trips/new", {"title": "<script>alert(1)</script>", "destination": '<img src=x onerror="alert(1)">', "body": '<script>alert("x")</script>', "visibility": "public"})
    for path in [response.headers["Location"], response.headers["Location"] + "/edit", "/", "/my-trips"]:
        html = client.get(path).get_data(as_text=True)
        assert "<script>" not in html
        assert "<img src=x" not in html
        assert "&lt;script&gt;" in html


def test_guest_reset_and_invalid_user(client, login, post):
    login(1)
    assert client.get("/my-trips").status_code == 200
    login(0)
    assert client.get("/my-trips").status_code == 403
    assert post("/demo-user", {"user_id": "999"}).status_code == 400
    assert post("/demo-user", {"user_id": "bad"}).status_code == 400


def test_headers_and_not_found(client):
    response = client.get("/trips/9999")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
