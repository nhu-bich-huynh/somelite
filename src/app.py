from flask import Flask
from flask_login import LoginManager

from database import Db

db = Db("somelite", admin_password="postgres")


def create_app():
    app = Flask(__name__)

    # python -c 'import secrets; print(secrets.token_hex())'
    app.config["SECRET_KEY"] = "password"

    # delete the old db if it exists
    print("recreating database")
    db.delete()
    db.create()
    db.create_tables()

    from auth import auth

    app.register_blueprint(auth)

    from main import main

    app.register_blueprint(main)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    return app
