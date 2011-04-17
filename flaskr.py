# -*- coding: utf-8 -*-
"""
    MySQLFlaskr
    ~~~~~~

    A microblog example application written as Flask tutorial with
    Flask and MySQL.

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
                                db='flaskr',
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
def show_entries():
    cur = g.db.cursor(DictCursor)
    query = 'select title, text from entries order by id desc'
    cur.execute(query)
    entries = [dict(title=row['title'].decode('utf-8'), text=row['text'].decode('utf-8')) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)


@application.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    cur = g.db.cursor()
    cur.execute('insert into entries (title, text) values(%s,%s)',
                [request.form['title'].encode('utf-8'), request.form['text'].encode('utf-8')])
    cur.close()
    g.db.commit()

    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@application.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != application.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != application.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    application.run()
