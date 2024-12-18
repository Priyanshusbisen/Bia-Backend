import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

def get_bool_env_var(env_var, default=False):
    return os.environ.get(env_var, str(default)).lower() in ['true', '1', 't']

class Config:
    
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    VERTEXAI_PROJECT_NAME = os.environ.get("VERTEXAI_PROJECT_NAME","interview-analysis-444315")
    VERTEXAI_LOCATION = os.environ.get('VERTEXAI_LOCATION','us-east1')
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME','bia-810')
    GCS_VIDEO_PATH = os.environ.get('GCS_VIDEO_PATH','recordings')
    

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

class ProductionConfig(Config):
    DEBUG = False
