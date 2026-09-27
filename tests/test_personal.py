import pytest
from app.database import open_database, initialize_database


def test_settings_persist_and_only_current_user(app, client, login, post):
    login(1)
    assert post('/settings', {'name':'旅好き','bio':'<script>test</script>','default_visibility':'public','user_id':'2'}).status_code == 302
    html = client.get('/my-trips').get_data(as_text=True)
    assert '旅好き' in html and '&lt;script&gt;' in html
    assert 'value="public" checked' in client.get('/trips/new').get_data(as_text=True)
    with open_database(app.config['DATABASE']) as db:
        assert db.execute('SELECT name FROM users WHERE id=2').fetchone()[0] == '参加者'
        assert db.execute('SELECT visibility FROM trips WHERE id=6').fetchone()[0] == 'private'


@pytest.mark.parametrize('name,bio,visibility',[('', '', 'private'),('x'*31,'','private'),('旅','x'*301,'private'),('旅','','friends')])
def test_settings_validation(login, post, name, bio, visibility):
    login(1)
    assert post('/settings',dict(name=name,bio=bio,default_visibility=visibility)).status_code == 400


def test_favorites_access_and_idempotency(app, client, login, post):
    login(2)
    assert post('/trips/5/favorite',{'action':'add'}).status_code == 302
    assert post('/trips/5/favorite',{'action':'add'}).status_code == 302
    assert 'グループ限定の散歩プラン' in client.get('/favorites').get_data(as_text=True)
    assert post('/trips/6/favorite',{'action':'add'}).status_code == 404
    login(3)
    assert 'グループ限定の散歩プラン' not in client.get('/favorites').get_data(as_text=True)
    assert post('/trips/5/favorite',{'action':'add'}).status_code == 404
    login(2)
    assert post('/groups',{'action':'leave','group_id':'1'}).status_code == 302
    assert 'グループ限定の散歩プラン' not in client.get('/favorites').get_data(as_text=True)
    assert client.get('/trips/5').status_code == 404
    assert post('/trips/5/favorite',{'action':'remove'}).status_code == 302
    with open_database(app.config['DATABASE']) as db:
        assert db.execute('SELECT COUNT(*) FROM favorites').fetchone()[0] == 0


def test_favorite_private_after_public(client, login, post):
    login(2)
    post('/trips/1/favorite',{'action':'add'})
    login(1)
    post('/trips/1/edit',{'title':'秘密の予定','destination':'山梨','body':'非公開本文','visibility':'private'})
    login(2)
    html = client.get('/favorites').get_data(as_text=True)
    assert '秘密の予定' not in html and '非公開本文' not in html


def test_personal_requires_login_and_csrf(client, login):
    assert client.get('/settings').status_code == 403
    assert client.get('/favorites').status_code == 403
    login(1)
    assert client.post('/settings',data={'name':'不正'}).status_code == 400
    assert client.post('/trips/1/favorite',data={'action':'add'}).status_code == 400


def test_saved_itinerary_survives_initialization(app):
    with open_database(app.config['DATABASE']) as db:
        db.execute("INSERT INTO itinerary(trip_id,day,time,title,place,note,position) VALUES (2,1,'09:00','保存した予定','集合場所','メモ',0)")
    initialize_database(app.config['DATABASE'])
    with open_database(app.config['DATABASE']) as db:
        assert db.execute('SELECT title FROM itinerary WHERE trip_id=2').fetchone()[0] == '保存した予定'


def test_inline_favorite_and_return_location(client, login, post):
    login(1)
    assert 'favorite-overlay' in client.get('/').get_data(as_text=True)
    response = post('/trips/1/favorite', {'action':'add'}, headers={'Accept':'application/json'})
    assert response.status_code == 200 and response.json == {'favorite':True}
    assert 'aria-pressed="true"' in client.get('/trips/1').get_data(as_text=True)
    response = post('/trips/1/favorite', {'action':'remove'}, headers={'Accept':'application/json'})
    assert response.status_code == 200 and response.json == {'favorite':False}
    response = post('/trips/1/favorite', {'action':'add','source':'search','query':'山梨'})
    assert response.headers['Location'].startswith('/?q=') and response.headers['Location'].endswith('#plans')
    response = post('/trips/1/favorite', {'action':'remove','source':'https://example.com'})
    assert response.headers['Location'] == '/trips/1'
