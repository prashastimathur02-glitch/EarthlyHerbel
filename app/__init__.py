from flask import Flask
from dotenv import load_dotenv

from app.config import Config


load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    from app.routes import main
    app.register_blueprint(main)

    return app