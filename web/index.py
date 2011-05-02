# -*- coding: utf-8 -*-
"""
    Watasync
    ~~~~~~~~

    A gaibu dennou.

    :copyright: (c) 2011 by rysk92.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import os.path
import MySQLdb
from MySQLdb.cursors import DictCursor
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

ROOTDIR = os.path.normpath(os.path.dirname(__file__) + "/../")
execfile(ROOTDIR + "/config.py")

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = G_CONFIG['user']['username']
PASSWORD = G_CONFIG['user']['password']

# create our little application :)
application = Flask(__name__)
application.config.from_object(__name__)
application.config.from_envvar('FLASKR_SETTINGS', silent=True)
application.default_config.DEBUG = True

def connect_db():
    """Returns a new connection to the database."""
    dbconnect = MySQLdb.connect(user=G_CONFIG['mysqldns']['user'],
                                passwd=G_CONFIG['mysqldns']['passwd'],
                                db=G_CONFIG['mysqldns']['name'],
                                host=G_CONFIG['mysqldns']['host'],
                                charset=G_CONFIG['mysqldns']['charset'],
                                unix_socket=G_CONFIG['mysqldns']['unix_socket'])

    return dbconnect


@application.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db()
    g.render_common_context = G_CONFIG['render_common_context']

@application.after_request
def after_request(response):
    """Closes the database again at the end of the request."""
    g.db.close()
    return response


@application.route('/', methods=['GET'])
def show_memos():
    keyword = request.args.get('keyword')
    
    page = request.args.get('page')
    if page is None:
      page = 1 
    else:
      page = int(page)
    if page < 1: page=1
    limit = 10
    offset = (page-1)*limit

    return render_template('show_memos.html', common=g.render_common_context, keyword=keyword, nextpage=page+1, page=page)


@application.route('/add', methods=['POST'])
def add_memo():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('insert into memo (memo,created_at,updated_at) values(%s,NOW(),NOW())',
                [request.form['value'].encode('utf-8')])
    cur.close()
    g.db.commit()

    flash("メモしたで(｀ω´)".decode('utf-8'))
    return redirect(url_for('show_memos'))

@application.route('/update', methods=['POST'])
def update_memo():
    if not session.get('logged_in'):
        abort(401)
    memo_id = request.form['id']
    cur = g.db.cursor()
    cur.execute('update memo set memo=%s, updated_at=NOW() where id=%s',
                [request.form['value'].encode('utf-8'),memo_id])
    cur.close()
    g.db.commit()
    
    cur = g.db.cursor(DictCursor)
    query = 'select id,memo,created_at from memo where id = %s'
    cur.execute(query, memo_id)

    result = cur.fetchone()
    memo = result['memo'].decode('utf-8')
    return render_template('memo.html', memo=memo)

@application.route('/updatetag', methods=['POST'])
def update_tag():
    if not session.get('logged_in'):
        abort(401)
    tag = request.form['tag'].encode('utf-8')
    memo_id = request.form['memo_id']
    cur = g.db.cursor()
    cur.execute('update memo set tag=%s, updated_at=NOW() where id=%s',
                [tag,memo_id])
    cur.close()
    g.db.commit()
    
    cur = g.db.cursor(DictCursor)
    query = 'select id,tag from memo where id = %s'
    cur.execute(query, memo_id)

    result = cur.fetchone()
    tag = result['tag'].decode('utf-8')
    return render_template('tag.html', tag=tag)

@application.route('/delete', methods=['POST'])
def delete_memo():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('insert into memo (memo,created_at,updated_at) values(%s,NOW(),NOW())',
                [request.form['memo'].encode('utf-8')])
    cur.close()
    g.db.commit()

    flash("メモしたで(｀ω´)".decode('utf-8'))
    return redirect(url_for('show_memos'))

@application.route('/memo/', methods=['GET'])
def show_memo():
    if not session.get('logged_in'):
        abort(401)
    memo_id = request.args.get('id')

    cur = g.db.cursor(DictCursor)
    query = 'select id,memo,created_at from memo where id = %s'
    cur.execute(query, memo_id)

    result = cur.fetchone()
    memo = result['memo'].decode('utf-8')
    return render_template('memo.html', memo=memo)

@application.route('/search/', methods=['GET'])
def search_memo():
    if not session.get('logged_in'):
        abort(401)
    keyword = request.args.get('keyword')

    page = request.args.get('page')
    if page is None:
      page = 1 
    else:
      page = int(page)
    if page < 1: page=1
    limit = 30
    offset = (page-1)*limit

    if keyword:
      cur = g.db.cursor(DictCursor)
      query = 'select id,memo,created_at from memo where memo like %s order by id desc limit %s offset %s'
      cur.execute(query, ("%" + str(keyword.encode('utf-8')) + "%", limit, offset))

      memos = [dict(id=row['id'],created_at=row['created_at'],memo=row['memo'].decode('utf-8')) for row in cur.fetchall()]

      cur = g.db.cursor(DictCursor)
      query = "select count(*) from memo where memo like %s"
      cur.execute(query, ("%" + str(keyword.encode('utf-8')) + "%"))
      count = cur.fetchone()['count(*)']
    else:
      cur = g.db.cursor(DictCursor)
      query = 'select id,memo,created_at from memo order by id desc limit %s offset %s'
      cur.execute(query, (limit, offset))

      memos = [dict(id=row['id'],created_at=row['created_at'],memo=row['memo'].decode('utf-8')) for row in cur.fetchall()]

      cur = g.db.cursor(DictCursor)
      query = "select count(*) from memo"
      cur.execute(query)
      count = cur.fetchone()['count(*)']

    return render_template('search.html', memos=memos, count=count)

@application.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != application.config['USERNAME']:
            error = 'ユーザ名が違うで(｀ω´)'.decode('utf-8')
        elif request.form['password'] != application.config['PASSWORD']:
            error = 'パスワードが違うで(｀ω´)'.decode('utf-8')
        else:
            session['logged_in'] = True
            flash("ログインしたで(｀ω´)".decode('utf-8'))
            return redirect(url_for('show_memos'))
    return render_template('login.html', common=g.render_common_context, error=error)


@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('ログアウトしたで(｀ω´)'.decode('utf-8'))
    return redirect(url_for('show_memos'))

if __name__ == '__main__':
    application.run()

