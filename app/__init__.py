from flask import Flask
from app.extentions import db, migrate, ma
from app.blueprints import api_bp
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from app.config import Config
import logging

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    print(Config.SQLALCHEMY_DATABASE_URI)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 50MB limit

    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        logger.error('SQLALCHEMY_DATABASE_URI is not set in configuration.')
        raise ValueError('SQLALCHEMY_DATABASE_URI is not set in configuration.')

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    cors = CORS(app, resources={r"*": {"origins": "*"}}) 
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    @app.route('/')
    def home():
        return "Hello, HTTPS!"
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    
    logger.info('Application initialized successfully.')

    return app
