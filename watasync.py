# -*- coding: utf-8 -*-
"""
    Watasync
    ~~~~~~~~

    A gaibu dennou.

    :copyright: (c) 2011 by rysk92.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import MySQLdb
from MySQLdb.cursors import DictCursor
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

# configuration
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
application = Flask(__name__)
application.config.from_object(__name__)
application.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Returns a new connection to the database."""
    dbconnect = MySQLdb.connect(user='root',
                                passwd='',
                                db='watasync',
                                host='localhost')

    return dbconnect


@application.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db()


@application.after_request
def after_request(response):
    """Closes the database again at the end of the request."""
    g.db.close()
    return response


@application.route('/')
def show_memos():
    cur = g.db.cursor(DictCursor)
    query = 'select memo,created_at from memo order by id desc'
    cur.execute(query)
    memos = [dict(memo=row['memo'].decode('utf-8'), created_at=row['created_at']) for row in cur.fetchall()]
    return render_template('show_memos.html', memos=memos)


@application.route('/add', methods=['POST'])
def add_memo():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('insert into memo (memo,created_at,updated_at) values(%s,NOW(),NOW())',
                [request.form['memo'].encode('utf-8')])
    cur.close()
    g.db.commit()

    flash("メモしたで(｀ω´)".decode('utf-8'))
    return redirect(url_for('show_memos'))


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
    return render_template('login.html', error=error)


@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('ログアウトしたで(｀ω´)'.decode('utf-8'))
    return redirect(url_for('show_memos'))


if __name__ == '__main__':
    application.run()
