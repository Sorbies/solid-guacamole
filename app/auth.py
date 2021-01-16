import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db, auth_methods

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        error = None
        username = request.form['register_username']
        password = request.form['register_password']
        confirm = request.form["confirm"]
        blog_name = request.form["blog_name"]
        description = request.form["description"]
        db = get_db()

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif auth_methods["check_username"](username):
            error = 'User "{}"\ is already registered.'.format(username)

        if error is None:
            auth_methods["add_user"](username, password, blog_name, description)
            return redirect(url_for('auth.login', error=error))
        return render_template('auth/register.html', error=error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "" or password == "":
            return render_template("auth/login.html", error="Please fill in your credentials")
        elif not auth_methods["check_credentials"](username, password):
            return render_template("auth/login.html", error="Wrong credentials!")
            
        session.clear()
        session["username"] = username
        session["password"] = password
        
    if("username" in session and "password" in session and auth_methods["check_credentials"](session["username"], session["password"])):
        return redirect(url_for('index'))

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# checks that a user is logged in, and redirects them if they are not
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view