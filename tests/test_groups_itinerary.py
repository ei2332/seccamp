import pytest
from app.database import initialize_database, open_database


def payload(**changes):
    return {"title": "新しいしおり", "destination": "山梨", "body": "架空の旅", "visibility": "private", **changes}


def test_itinerary_roundtrip_and_order(client, login, post):
    login(1)
    data = payload(step_day=["2", "1", "1"], step_time=["10:00", "", "09:00"],
                   step_title=["美術館", "散歩", "集合"], step_place=["展示室", "", "駅"],
                   step_note=["ゆっくり", "", "<script>alert(1)</script>"])
    response = post("/trips/new", data)
    assert response.status_code == 302
    location = response.headers["Location"]
    html = client.get(location).get_data(as_text=True)
    assert html.index("集合") < html.index("散歩") < html.index("美術館")
    assert "&lt;script&gt;" in html and "<script>alert" not in html
    edit = client.get(location + "/edit").get_data(as_text=True)
    assert 'value="美術館"' in edit and 'value="09:00"' in edit
    data.update(step_day=["1"], step_time=["12:00"], step_title=["ランチ"], step_place=["カフェ"], step_note=["予約不要"])
    assert post(location + "/edit", data).status_code == 302
    html = client.get(location).get_data(as_text=True)
    assert "ランチ" in html and "美術館" not in html
    assert post(location + "/edit", payload()).status_code == 302
    assert "予定はこれから" in client.get(location).get_data(as_text=True)


@pytest.mark.parametrize("change", [
    {"step_day": "0"}, {"step_day": "31"}, {"step_day": "no"},
    {"step_time": "25:00"}, {"step_title": ""}, {"step_title": "x"*101},
    {"step_place": "x"*101}, {"step_note": "x"*1001}, {"step_day": ["1","2"]},
])
def test_invalid_steps_are_not_saved(app, login, post, change):
    login(1)
    data = payload(step_day="1", step_time="10:00", step_title="予定", step_place="駅", step_note="メモ")
    data.update(change)
    with open_database(app.config["DATABASE"]) as db:
        before_count = db.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    assert post("/trips/new", data).status_code == 400
    with open_database(app.config["DATABASE"]) as db:
        assert db.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == before_count


def test_only_joined_groups_can_be_selected(app, client, login, post):
    login(3)
    html = client.get("/trips/new").get_data(as_text=True)
    assert "テストグループ" not in html
    assert post("/trips/new", payload(visibility="friends", group_id="1")).status_code == 400
    assert post("/trips/new", payload(visibility="friends", group_id="999")).status_code == 400
    assert post("/trips/new", payload(visibility="friends")).status_code == 400
    assert post("/groups", {"action": "join", "invite_code": "bad"}).status_code == 400
    with open_database(app.config["DATABASE"]) as db:
        code = db.execute("SELECT invite_code FROM travel_groups WHERE id = 1").fetchone()[0]
    assert code not in client.get("/groups").get_data(as_text=True)
    assert post("/groups", {"action": "join", "invite_code": code}).status_code == 302
    assert post("/groups", {"action": "join", "invite_code": code}).status_code == 302
    assert client.get("/trips/5").status_code == 200
    assert client.get("/trips/5/edit").status_code == 404
    assert code not in client.get("/groups").get_data(as_text=True)
    assert post("/groups", {"action": "leave", "group_id": "1"}).status_code == 302
    assert client.get("/trips/5").status_code == 404
    assert "グループ限定の散歩プラン" not in client.get("/my-trips").get_data(as_text=True)


def test_group_creation_owner_and_csrf(client, login, post):
    assert client.get("/groups").status_code == 403
    login(1)
    assert client.post("/groups", data={"action": "create", "name": "no csrf"}).status_code == 400
    assert post("/groups", {"action": "create", "name": ""}).status_code == 400
    assert post("/groups", {"action": "create", "name": "<script>旅</script>"}).status_code == 302
    html = client.get("/groups").get_data(as_text=True)
    assert "&lt;script&gt;旅&lt;/script&gt;" in html
    assert post("/groups", {"action": "leave", "group_id": "1"}).status_code == 400
    assert client.get("/trips/5").status_code == 200


def test_initialization_preserves_data_and_members(app):
    path = app.config["DATABASE"]
    with open_database(path) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        db.execute("UPDATE trips SET title='変更した旅', body='保存した本文' WHERE id=5")
        db.execute("UPDATE users SET bio='自己紹介', default_visibility='public' WHERE id=1")
        db.execute("INSERT INTO favorites VALUES(1,2)")
        db.execute("INSERT INTO group_members VALUES(1,3)")
        db.commit()
        before = {table: list(db.execute(f"SELECT * FROM {table} ORDER BY rowid")) for table in tables}
    initialize_database(path)
    initialize_database(path)
    with open_database(path) as db:
        after = {table: list(db.execute(f"SELECT * FROM {table} ORDER BY rowid")) for table in tables}
        assert after == before
