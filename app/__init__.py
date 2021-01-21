import os

from flask import Flask, render_template, g, url_for, redirect, render_template

#When you run as a dev you need to specify host - 0.0.0.0 so everyone can see it

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.urandom(32),
        DATABASE=os.path.join(app.instance_path, 'data.db'),
    )
    with app.app_context():
        # ensure the instance folder exists
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass

        from . import db_builder, auth, blog, follow, search
        #db_builder.init_app(app)
        app.register_blueprint(auth.bp)
        app.register_blueprint(blog.bp)
        app.register_blueprint(follow.bp)
        app.register_blueprint(search.bp)

        # if user tries to access page that doesn't exist
        @app.errorhandler(404)
        def error404(e):
            # return page not found template if user is logged in
            if g.user is None:
                return render_template("error/404.html", code=404)
            # otherwise redirect user to login page
            return redirect(url_for("auth.login"))

        app.add_url_rule('/', endpoint='index')
        return app