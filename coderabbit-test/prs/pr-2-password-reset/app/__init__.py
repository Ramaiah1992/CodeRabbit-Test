from flask import Flask

from app.config import Config
from app.db import init_db
from app.routes.password_reset import bp as password_reset_bp
from app.routes.tasks import bp as tasks_bp
from app.routes.users import bp as users_bp


def create_app(config=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    init_db(app.config["DB_PATH"])

    app.register_blueprint(users_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(password_reset_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
