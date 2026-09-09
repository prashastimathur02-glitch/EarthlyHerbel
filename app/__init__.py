from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin

from app.config import Config
from app.database import get_db_connection


load_dotenv()


login_manager = LoginManager()
login_manager.login_view = "main.login"


class User(UserMixin):

    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email


@login_manager.user_loader
def load_user(user_id):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, name, email
                FROM customers
                WHERE id = %s
                """,
                (user_id,)
            )

            row = cursor.fetchone()

    finally:
        connection.close()

    if row is None:
        return None

    return User(
        row[0],
        row[1],
        row[2]
    )


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    login_manager.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app