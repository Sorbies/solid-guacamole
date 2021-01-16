import os

from flask import Flask, render_template, g, url_for

#When you run as a dev you need to specify host - 0.0.0.0 so everyone can see it

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.urandom(32),
        DATABASE=os.path.join(app.instance_path, 'fruit_for_blogs.db'),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
 
    from . import db, auth
    db.init_app(app)
    app.register_blueprint(auth.bp)

    # routing here
    @app.route('/')
    def root():
        return render_template("auth/login_or_register.html")

    @app.errorhandler(404)
    def error404():
        if user in g:
            return "hi. 404."
        return redirect(url_for('auth.login'))
    
    return app