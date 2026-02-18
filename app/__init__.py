from flask import Flask
from config import Config, TestConfig
from app.extensions import db, login_manager


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.shop import shop_bp
    from app.routes.order import order_bp
    from app.routes.user import user_bp
    from app.routes.notification import notification_bp
    from app.routes.statistics import statistics_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(order_bp, url_prefix='/order')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(notification_bp, url_prefix='/notification')
    app.register_blueprint(statistics_bp, url_prefix='/statistics')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
