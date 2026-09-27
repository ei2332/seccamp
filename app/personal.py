"""個人設定とお気に入り。お気に入りは閲覧権限を付与しない。"""
from flask import abort, g, jsonify, redirect, render_template, request, url_for



def register_personal(app, database, require_user, find_trip):
    @app.context_processor
    def favorite_context():
        return {'favorite_ids': {row['trip_id'] for row in database().execute('SELECT trip_id FROM favorites WHERE user_id=?', (g.user['id'],))} if g.get('user') else set()}

    @app.route('/settings', methods=['GET','POST'])
    def settings():
        user_id = require_user()
        values = dict(database().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone())
        error = None
        if request.method == 'POST':
            values = {key:request.form.get(key,'').strip() for key in ('name','bio','default_visibility')}
            if not 1 <= len(values['name']) <= 30 or len(values['bio']) > 300 or values['default_visibility'] not in ('public','private'):
                error = '表示名は1〜30字、自己紹介は300字以内で入力し、初期公開範囲を選んでください。'
            else:
                with database() as db:
                    db.execute('UPDATE users SET name=?,bio=?,default_visibility=? WHERE id=?', (values['name'],values['bio'],values['default_visibility'],user_id))
                return redirect(url_for('settings', saved='1'))
        return render_template('settings.html', values=values, error=error, saved=request.args.get('saved') == '1'), 400 if error else 200

    @app.get('/favorites')
    def favorites():
        user_id = require_user()
        trips = database().execute("SELECT trips.* FROM trips JOIN favorites ON favorites.trip_id=trips.id WHERE favorites.user_id=? AND (visibility='public' OR owner_id=? OR (visibility='friends' AND EXISTS (SELECT 1 FROM group_members WHERE group_members.group_id=trips.group_id AND group_members.user_id=?))) ORDER BY trips.id DESC", (user_id,user_id,user_id)).fetchall()
        return render_template('favorites.html', trips=trips)

    @app.post('/trips/<int:trip_id>/favorite')
    def toggle_favorite(trip_id):
        user_id = require_user()
        action = request.form.get('action')
        if action not in ('add','remove'):
            abort(400)
        if action == 'add':
            find_trip(trip_id)
        with database() as db:
            if action == 'add':
                db.execute('INSERT OR IGNORE INTO favorites VALUES (?,?)', (user_id,trip_id))
            else:
                db.execute('DELETE FROM favorites WHERE user_id=? AND trip_id=?', (user_id,trip_id))
        if request.headers.get('Accept') == 'application/json':
            return jsonify(favorite=action == 'add')
        # JSが動かない場合も、外部URLを受け取らず元の種類のページへ戻す。
        source = request.form.get('source')
        if source == 'search':
            return redirect(url_for('search', q=request.form.get('query',''), _anchor='plans'))
        if source in ('my_trips', 'favorites'):
            return redirect(url_for(source))
        return redirect(url_for('trip_detail', trip_id=trip_id))
