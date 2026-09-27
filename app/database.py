"""SQLiteへの接続、スキーマの初期化とサンプルデータの登録。"""

import secrets
import sqlite3
from contextlib import closing

from app.sample_itineraries import SAMPLES


def open_database(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize_database(path, *, seed_samples=True):
    with closing(open_database(path)) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                bio TEXT NOT NULL DEFAULT '',
                default_visibility TEXT NOT NULL DEFAULT 'private'
            );
            CREATE TABLE IF NOT EXISTS travel_groups (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                invite_code TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                destination TEXT NOT NULL, body TEXT NOT NULL,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                visibility TEXT NOT NULL CHECK (visibility IN ('public','friends','private')),
                group_id INTEGER REFERENCES travel_groups(id)
            );
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL REFERENCES travel_groups(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                PRIMARY KEY(group_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS itinerary (
                id INTEGER PRIMARY KEY, trip_id INTEGER NOT NULL REFERENCES trips(id),
                day INTEGER NOT NULL, time TEXT NOT NULL, title TEXT NOT NULL,
                place TEXT NOT NULL, note TEXT NOT NULL, position INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL REFERENCES users(id),
                trip_id INTEGER NOT NULL REFERENCES trips(id),
                PRIMARY KEY(user_id, trip_id)
            );
        """)
        if not seed_samples or db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            return
        db.executemany("INSERT INTO users(id,name) VALUES (?, ?)", [(1, "はる"), (2, "あおい"), (3, "れん")])
        db.executemany("INSERT INTO trips(id,title,destination,body,owner_id,visibility) VALUES (?, ?, ?, ?, ?, ?)", [
            (1, "山梨で湖とカフェを巡る週末", "山梨・河口湖", "1日目：湖畔を散歩してカフェへ。\n2日目：美術館と地元のごはんを楽しむ。", 1, "public"),
            (2, "O'Reillyの本と過ごす読書旅", "長野・軽井沢", "本を片手に小さな宿へ。\n午前は読書、午後は森の中を散歩する。", 2, "public"),
            (3, "京都の路地を歩く日帰り旅", "京都", "朝は市場、昼は路地の喫茶店へ。\n夕方は川沿いで休憩する。", 3, "public"),
            (4, "星空と朝のコーヒーを楽しむキャンプ", "静岡・朝霧高原", "テントと食材の準備が完了。\n夜は星を眺めて、翌朝はゆっくり朝食。", 1, "public"),
            (5, "山梨ドライブの集合計画", "山梨", "架空の集合情報：土曜9時にサンプル駅北口。\nはる・あおいで費用と持ち物を相談する。", 1, "friends"),
            (6, "次の一人旅の下書き", "北海道", "架空の個人メモ：予算は3万円。\nまだ決めていない候補の宿と予定を整理する。", 1, "private"),
        ])
        db.execute("INSERT INTO travel_groups(id,name,owner_id,invite_code) VALUES (1,?,?,?)",
                   ("週末旅の仲間", 1, secrets.token_urlsafe(18)))
        db.executemany("INSERT INTO group_members(group_id,user_id) VALUES (1,?)", [(1,), (2,)])
        db.execute("UPDATE trips SET group_id=1 WHERE id=5")
        for trip_id, steps in SAMPLES.items():
            db.executemany(
                "INSERT INTO itinerary(trip_id,day,time,title,place,note,position) VALUES (?,?,?,?,?,?,?)",
                [(trip_id, *step, position) for position, step in enumerate(steps)],
            )
