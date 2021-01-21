import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db_builder import auth_methods, validateInput, pageEntries, get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# checks that a user is logged in, and redirects them if they are not
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

# checks that a user is not logged in, and redirects them if they are not
def login_unrequired(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is not None:
            return redirect(url_for('blog.homepage'))

        return view(**kwargs)

    return wrapped_view
    
@bp.before_app_request
def load_logged_in_user():
    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

@bp.route("/register", methods=["GET", "POST"])
@login_unrequired
def register():
    # if logged in user goes to register page, redirect to home page
    if "username" in session:
        return redirect(url_for('blog.homepage'))

    # if user has submitted registration form
    if "register" in request.form:
        error_msg = []
        # checks username is valid
        username = validateInput("username", request.form["username"], error_msg)
        # checks password is valid
        password = validateInput("password", request.form["password"], error_msg)
        # checks both passwords match
        if request.form["password-conf"] != password:
            error_msg += ["Passwords do not match"]
        # checks blog name is valid
        blogname = validateInput("blogname", request.form["blogname"], error_msg)
        # checks blog description is valid
        blogdescription = validateInput("blogdescription", request.form["blogdescription"], error_msg)
        # reloads register form with error msgs and blog name/description filled out
        if error_msg:
            session["error_msg"] = "Unsuccessful registration"
            return render_template("auth/register.html", error_msg=error_msg, blogname=blogname,
                                   blogdescription=blogdescription)
        else:
            # adds user to database
            auth_methods["addUser"](username, password, blogname, blogdescription)
            session["error_msg"] = "Successful registration"
            # when a user has just registered, their information is present in the login form
            # however, url_for uses the GET method, which displays the username/password in the url,
            # so specifying the code ensures that the original method (POST) is used
            return redirect(url_for("auth.login"), code=307)

    # if user hasn't submitted reg form yet
    return render_template("auth/register.html")

@bp.route("/login", methods=["GET", "POST"])
@login_unrequired
def login():
    if request.method == 'POST':
        if "error_msg" not in session:
            session["error_msg"] = ""

        # if user is already logged in
        if "username" in session:
            # redirect to home page
            return redirect(url_for("blog.homepage"))

    # if user submitted registration form
    if "register" in request.form:
        # if user has successfully registered, have info in login form
        if session["error_msg"] == "Successful registration":
            session.pop("error_msg")
            return render_template("auth/login.html", username=request.form["username"], password=request.form["password"],
                                error_msg="Successful registration")
        # if user submits reg form, encounters error, and goes to login page
        elif session["error_msg"] == "Unsuccessful registration":
            session.pop("error_msg")
            return render_template("auth/login.html")

    # if user is trying to log in
    if "login" in request.form:
        # if username doesn't exist in the database
        if not auth_methods["checkUsername"](request.form["username"]):
            # set error msg in session
            session["error_msg"] = "Incorrect username or password."
        else: 
            password = auth_methods["getPwd"](request.form["username"], "password")    # get correct password for user from database
            newPassword = check_password_hash(password, request.form["password"] + auth_methods["salt"])

            # if password is correct
            if newPassword:
                # set username/password in session if successful login
                session["username"] = request.form["username"]
                session["password"] = request.form["password"]
                session["error_msg"] = ""
                # return home page for user
                return redirect(url_for("blog.homepage")) #add blog.homepage

            # if password is incorrect
            else:
                # if incorrect login, set error msg in session
                session["error_msg"] = "Incorrect username or password."

        # if there is an error in user login, display error
        if session["error_msg"] == "Incorrect username or password.":
            return render_template("auth/login.html", username=request.form.get("username", ""),
                                error_msg="Incorrect username or password.")
    return render_template("auth/login.html")

    # if user tries to access page without being logged in, render login page
    return render_template("auth/login.html")

@bp.route("/logout")
@login_required
def logout():
    session.pop("username")
    session.pop("password")
    g.user = None
    # log user out, return to login page with log out msg displayed
    return render_template("auth/login.html", error_msg="Successfully logged out.")