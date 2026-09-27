"""旅のしおりのアプリケーション設定と公開プラン検索。"""

import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, render_template, request

from app.database import initialize_database, open_database
from app.views import register_views


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / "travel.sqlite3"),
        TRAVEL_GUIDE_DIR=str(Path(app.root_path) / "travel_guides"),
        MAX_CONTENT_LENGTH=32_768,
        SEED_SAMPLE_DATA=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    initialize_database(app.config["DATABASE"], seed_samples=app.config["SEED_SAMPLE_DATA"])
    register_views(app)

    @app.get("/")
    def search():
        query = request.args.get("q", "")
        # 部分一致検索では、入力中の % と _ も通常の文字として扱う。
        term = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with closing(open_database(app.config["DATABASE"])) as db:
            sql = f"SELECT id, title, destination, body, visibility FROM trips WHERE visibility = 'public' AND title LIKE '%{term}%' ESCAPE '\\' ORDER BY id"
            try:
                trips = db.execute(sql).fetchall()
            except sqlite3.Error:
                return render_template("search.html", query=query, trips=[], error="検索できませんでした。"), 400
        return render_template("search.html", query=query, trips=trips, error=None)

    return app
