"""旅行プランの印刷表示と、旅の準備資料のダウンロード。"""

import os

import flask
from flask import Response, abort, render_template


def register_travel_tools(app, database, find_trip):
    @app.get("/trips/<int:trip_id>/print")
    def print_trip(trip_id):
        trip = find_trip(trip_id)
        heading = flask.request.args.get("heading", trip["title"])
        heading_html = f"<h1>{heading}</h1>"
        steps = database().execute(
            "SELECT * FROM itinerary WHERE trip_id = ? ORDER BY day, time, position",
            (trip_id,),
        ).fetchall()
        return render_template("print.html", trip=trip, steps=steps, heading_html=heading_html)

    @app.get("/travel-guides/download")
    def download_travel_guide():
        path = os.path.join(app.config["TRAVEL_GUIDE_DIR"], flask.request.args.get("name", "packing-list.txt"))
        try:
            with open(path, encoding="utf-8") as guide:
                content = guide.read()
        except (OSError, UnicodeError, ValueError):
            abort(404)
        return Response(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="travel-guide.txt"'},
        )
