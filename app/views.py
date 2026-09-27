"""プランの閲覧・編集、公開範囲の制御とデモ利用者の切り替え。"""

import secrets

from flask import abort, g, redirect, render_template, request, session, url_for

from app.database import open_database
from app.groups import register_groups
from app.itinerary import read_steps
from app.personal import register_personal
from app.travel_tools import register_travel_tools

VISIBILITIES = {"public": "全体公開", "friends": "グループ限定", "private": "自分限定"}


def register_views(app):
    def database():
        if "db" not in g:
            g.db = open_database(app.config["DATABASE"])
        return g.db

    @app.teardown_appcontext
    def close_database(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def prepare_request():
        g.user = database().execute("SELECT * FROM users WHERE id = ?", (session.get("user_id"),)).fetchone()
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            provided = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), provided.encode()):
                abort(400)
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        return response

    @app.context_processor
    def shared_context():
        # エラーページでもCSRFトークンを用意する。
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return {"viewer": g.get("user"), "users": database().execute("SELECT * FROM users ORDER BY id").fetchall(), "visibilities": VISIBILITIES, "csrf_token": session["csrf_token"]}

    def require_user():
        if g.user is None:
            abort(403)
        return g.user["id"]

    register_groups(app, database, require_user)

    def find_trip(trip_id, edit=False):
        trip = database().execute("SELECT trips.*, users.name AS owner_name FROM trips JOIN users ON users.id = trips.owner_id WHERE trips.id = ?", (trip_id,)).fetchone()
        if trip is None:
            abort(404)
        user_id = g.user["id"] if g.user else None
        owner = user_id == trip["owner_id"]
        member = database().execute("SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?", (trip["group_id"], user_id)).fetchone()
        if edit and not owner:
            abort(404)
        if not edit and not (owner or trip["visibility"] == "public" or (trip["visibility"] == "friends" and member)):
            abort(404)
        return trip

    register_personal(app, database, require_user, find_trip)
    register_travel_tools(app, database, find_trip)

    @app.post("/demo-user")
    def switch_demo_user():
        # Privateポート内で架空の利用者の視点を切り替える。実サービスのログインではない。
        user_id = request.form.get("user_id", type=int)
        if user_id != 0 and not database().execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone():
            abort(400)
        session.clear()
        if user_id:
            session["user_id"] = user_id
        return redirect(url_for("search"))

    @app.get("/my-trips")
    def my_trips():
        user_id = require_user()
        trips = database().execute("SELECT * FROM trips WHERE owner_id = ? ORDER BY id DESC", (user_id,)).fetchall()
        shared = database().execute("SELECT trips.* FROM trips JOIN group_members ON trips.group_id = group_members.group_id WHERE group_members.user_id = ? AND visibility = 'friends' AND owner_id != ? ORDER BY trips.id DESC", (user_id, user_id)).fetchall()
        return render_template("my_trips.html", trips=trips, shared=shared)

    @app.get("/trips/<int:trip_id>")
    def trip_detail(trip_id):
        trip = find_trip(trip_id)
        group = None
        members = []
        if trip["visibility"] == "friends" and trip["group_id"]:
            group = database().execute("SELECT id,name FROM travel_groups WHERE id = ?", (trip["group_id"],)).fetchone()
            members = database().execute("SELECT users.name FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_id = ? ORDER BY users.id", (trip["group_id"],)).fetchall()
        steps = database().execute("SELECT * FROM itinerary WHERE trip_id = ? ORDER BY day, CASE WHEN time = '' THEN 1 ELSE 0 END, time, position", (trip_id,)).fetchall()
        favorite = database().execute('SELECT 1 FROM favorites WHERE user_id=? AND trip_id=?', (g.user['id'] if g.user else None,trip_id)).fetchone() is not None
        return render_template("detail.html", trip=trip, members=members, group=group, steps=steps, favorite=favorite)

    def trip_form(trip=None):
        user_id = require_user()
        groups = database().execute("SELECT travel_groups.id,travel_groups.name FROM travel_groups JOIN group_members ON group_members.group_id = travel_groups.id WHERE user_id = ? ORDER BY travel_groups.id", (user_id,)).fetchall()
        group_members = {group["id"]: database().execute("SELECT users.name FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_id = ?", (group["id"],)).fetchall() for group in groups}
        values = dict(trip) if trip else {"title": "", "destination": "", "body": "", "visibility": g.user['default_visibility'], "group_id": ""}
        steps = [dict(row) for row in database().execute("SELECT * FROM itinerary WHERE trip_id = ? ORDER BY day,time,position", (trip["id"] if trip else None,))]
        error = None
        if request.method == "POST":
            values = {key: request.form.get(key, "").strip() for key in ("title", "destination", "body", "visibility", "group_id")}
            steps, step_error = read_steps(request.form)
            valid_groups = {str(group["id"]) for group in groups}
            if any(not values[key] or len(values[key]) > limit for key, limit in (("title", 100), ("destination", 100), ("body", 4000))):
                error = "タイトル・行き先・概要を入力してください（100字・100字・4000字以内）。"
            elif values["visibility"] not in VISIBILITIES or (values["visibility"] == "friends" and values["group_id"] not in valid_groups):
                error = "参加している共有先グループを選んでください。"
            elif request.form.getlist("members"):
                error = "個人への共有は終了しました。グループを選んでください。"
            elif step_error:
                error = step_error
            else:
                group_id = int(values["group_id"]) if values["visibility"] == "friends" else None
                with database() as db:
                    if trip:
                        trip_id = trip["id"]
                        db.execute("UPDATE trips SET title = ?, destination = ?, body = ?, visibility = ?, group_id = ? WHERE id = ? AND owner_id = ?", (values["title"], values["destination"], values["body"], values["visibility"], group_id, trip_id, user_id))
                    else:
                        trip_id = db.execute("INSERT INTO trips (title,destination,body,visibility,group_id,owner_id) VALUES (?,?,?,?,?,?)", (values["title"],values["destination"],values["body"],values["visibility"],group_id,user_id)).lastrowid
                    db.execute("DELETE FROM itinerary WHERE trip_id = ?", (trip_id,))
                    db.executemany("INSERT INTO itinerary(trip_id,day,time,title,place,note,position) VALUES (?,?,?,?,?,?,?)", [(trip_id,int(item["day"]),item["time"],item["title"],item["place"],item["note"],i) for i,item in enumerate(steps)])
                return redirect(url_for("trip_detail", trip_id=trip_id))
        return render_template("form.html", trip=trip, values=values, groups=groups, group_members=group_members, steps=steps, error=error), 400 if error else 200

    @app.route("/trips/new", methods=["GET", "POST"])
    def create_trip():
        return trip_form()

    @app.route("/trips/<int:trip_id>/edit", methods=["GET", "POST"])
    def edit_trip(trip_id):
        require_user()
        return trip_form(find_trip(trip_id, edit=True))

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error_page(error):
        return render_template("error.html", status=error.code), error.code
