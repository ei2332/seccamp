"""招待コードによるグループへの参加とメンバー管理。"""
import secrets
from flask import abort, redirect, render_template, request, url_for


def register_groups(app, database, require_user):
    @app.route('/groups', methods=['GET', 'POST'])
    def groups():
        user_id = require_user()
        error = None
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'create':
                name = request.form.get('name', '').strip()
                if not name or len(name) > 60:
                    error = 'グループ名を60字以内で入力してください。'
                else:
                    with database() as db:
                        group_id = db.execute('INSERT INTO travel_groups(name,owner_id,invite_code) VALUES (?,?,?)', (name,user_id,secrets.token_urlsafe(18))).lastrowid
                        db.execute('INSERT INTO group_members VALUES (?,?)', (group_id,user_id))
                    return redirect(url_for('groups'))
            elif action == 'join':
                code = request.form.get('invite_code', '').strip()
                group = database().execute('SELECT id FROM travel_groups WHERE invite_code = ?', (code,)).fetchone()
                if group is None:
                    error = '招待コードを確認してください。'
                else:
                    with database() as db:
                        db.execute('INSERT OR IGNORE INTO group_members VALUES (?,?)', (group['id'],user_id))
                    return redirect(url_for('groups'))
            elif action == 'leave':
                group_id = request.form.get('group_id', type=int)
                group = database().execute('SELECT * FROM travel_groups WHERE id = ?', (group_id,)).fetchone()
                if group is None:
                    abort(404)
                if group['owner_id'] == user_id:
                    error = '作成者はグループを退出できません。'
                else:
                    with database() as db:
                        db.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id,user_id))
                    return redirect(url_for('groups'))
            else:
                abort(400)
        joined = database().execute('SELECT travel_groups.* FROM travel_groups JOIN group_members ON group_members.group_id = travel_groups.id WHERE user_id = ? ORDER BY travel_groups.id', (user_id,)).fetchall()
        members = {group['id']: database().execute('SELECT users.name FROM users JOIN group_members ON users.id = group_members.user_id WHERE group_id = ? ORDER BY users.id', (group['id'],)).fetchall() for group in joined}
        return render_template('groups.html', groups=joined, members=members, error=error), 400 if error else 200
