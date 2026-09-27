import pytest

from app.main import create_app
from app.database import open_database


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3"), "SEED_SAMPLE_DATA": False})
    with open_database(app.config["DATABASE"]) as db:
        db.executemany("INSERT INTO users(id,name) VALUES (?,?)", [(1, "作成者"), (2, "参加者"), (3, "第三者")])
        db.execute("INSERT INTO travel_groups(id,name,owner_id,invite_code) VALUES (1,'テストグループ',1,'test-invite-code')")
        db.executemany("INSERT INTO group_members VALUES (1,?)", [(1,), (2,)])
        db.executemany(
            "INSERT INTO trips(id,title,destination,body,owner_id,visibility,group_id) VALUES (?,?,?,?,?,?,?)",
            [
                (1, "公開の散歩プラン", "テスト市", "公開の本文", 1, "public", None),
                (2, "O'Reillyの読書プラン", "テスト市", "読書の本文", 2, "public", None),
                (3, "別の公開プラン", "テスト市", "別の本文", 3, "public", None),
                (4, "達成率100%_のプラン", "テスト市", "特殊文字の本文", 1, "public", None),
                (5, "グループ限定の散歩プラン", "テスト市", "グループ専用の本文", 1, "friends", 1),
                (6, "自分限定の散歩プラン", "テスト市", "自分専用の本文", 1, "private", None),
            ],
        )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def post(client):
    def submit(path, data=None, **kwargs):
        client.get("/")
        with client.session_transaction() as session:
            token = session["csrf_token"]
        return client.post(path, data={**(data or {}), "csrf_token": token}, **kwargs)
    return submit


@pytest.fixture
def login(post):
    def switch(user_id):
        return post("/demo-user", {"user_id": str(user_id)})
    return switch
