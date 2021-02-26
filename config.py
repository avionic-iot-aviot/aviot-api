import datetime
import os

class Config(object):
    DEBUG = False

    # for JWT token
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") if os.getenv("JWT_SECRET_KEY") is not None else "gHyJk89LoP0sCqQwErtF"
    if os.getenv("JWT_TOKEN_TTL"):
        JWT_EXPIRATION_DELTA = datetime.timedelta(seconds=int(os.getenv("JWT_SECRET_KEY")))
    else:
        JWT_EXPIRATION_DELTA = datetime.timedelta(seconds=3600)

    # for storing images and videos
    URL_IMGS = os.getenv("IMG_STORE_URL") if os.getenv("IMG_STORE_URL") is not None else "http://192.168.100.214/imgs/"

    URL_VIDEOS = os.getenv("VIDEO_STORE_URL") if os.getenv(
        "VIDEO_STORE_URL") is not None else "http://192.168.100.214/videos/"

    PATH_IMGS = os.getenv("PAT_IMGS") if os.getenv(
        "PAT_IMGS") is not None else "/home/michele/software-projects/video-streaming-janus-api/app/videos_and_images/imgs"

    PATH_VIDEOS = os.getenv("PATH_VIDEOS") if os.getenv(
        "PATH_VIDEOS") is not None else "/home/michele/software-projects/video-streaming-janus-api/app/videos_and_images/videos"

    # HTTPS flask
    HTTPS_FLASK_KEY = os.getenv("HTTPS_FLASK_KEY") if os.getenv(
        "HTTPS_FLASK_KEY") is not None else "/home/michele/software-projects/video-streaming-janus-api/certs/flask/key.pem"
    HTTPS_FLASK_CERT = os.getenv("HTTPS_FLASK_CERT") if os.getenv(
        "HTTPS_FLASK_CERT") is not None else "/home/michele/software-projects/video-streaming-janus-api/certs/flask/cert.pem"

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    JANUS_RESTAPI_SETTINGS = {
        'schema': "http",
        'host': os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "192.168.1.24",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'path': os.getenv("JANUS_SERVICE_PATH") if os.getenv("JANUS_SERVICE_PATH") is not None else "/janus",
        'api_secret': os.getenv("JANUS_API_SECRET") if os.getenv("JANUS_API_SECRET") is not None else "janusrocks"
    }

    JANUS_STREAM_SETTINGS = {
        "server": os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "192.168.1.24",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'ip': os.getenv("JANUS_SERVICE_IP") if os.getenv("JANUS_SERVICE_IP") is not None else "10.11.0.3",
        "schema": 'http'
    }

    ROS_SETTINGS = {
        'server': os.getenv("ROS_MASTER_SERVICE_HOST") if os.getenv(
            "ROS_MASTER_SERVICE_HOST") is not None else "127.0.0.1",
        'port': int(os.getenv("ROS_MASTER_SERVICE_PORT")) if os.getenv(
            "ROS_MASTER_SERVICE_PORT") is not None else 39237,

    }
    MONGODB_SETTINGS = {
        'db': os.getenv("MONGODB_DATABASE_NAME") if os.getenv("MONGODB_DATABASE_NAME") is not None else 'streamingdb',
        'host': os.getenv("MONGODB_SERVICE_HOST") if os.getenv("MONGODB_SERVICE_HOST") is not None else 'localhost',
        'port': int(os.getenv("MONGODB_SERVICE_PORT")) if os.getenv("MONGODB_SERVICE_PORT") is not None else 27017
    }


class DevelopmentConfig(Config):
    DEBUG = True

    JANUS_RESTAPI_SETTINGS = {
        'schema': "http",
        'host': os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "192.168.1.24",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'path': os.getenv("JANUS_SERVICE_PATH") if os.getenv("JANUS_SERVICE_PATH") is not None else "/janus",
        'api_secret': os.getenv("JANUS_API_SECRET") if os.getenv("JANUS_API_SECRET") is not None else "janusrocks"
    }

    JANUS_STREAM_SETTINGS = {
        "server": os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "192.168.1.24",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'ip': os.getenv("JANUS_SERVICE_IP") if os.getenv("JANUS_SERVICE_IP") is not None else "10.11.0.3",
        "schema": 'http'
    }

    ROS_SETTINGS = {
        'server': os.getenv("ROS_MASTER_SERVICE_HOST") if os.getenv(
            "ROS_MASTER_SERVICE_HOST") is not None else "127.0.0.1",
        'port': int(os.getenv("ROS_MASTER_SERVICE_PORT")) if os.getenv(
            "ROS_MASTER_SERVICE_PORT") is not None else 39237,

    }
    MONGODB_SETTINGS = {
        'db': os.getenv("MONGODB_DATABASE_NAME") if os.getenv("MONGODB_DATABASE_NAME") is not None else 'streamingdb',
        'host': os.getenv("MONGODB_SERVICE_HOST") if os.getenv("MONGODB_SERVICE_HOST") is not None else 'localhost',
        'port': int(os.getenv("MONGODB_SERVICE_PORT")) if os.getenv("MONGODB_SERVICE_PORT") is not None else 27017
    }


class TestingConfig(Config):

    DEBUG = True
    JANUS_RESTAPI_SETTINGS = {
        'schema': "http",
        'host': os.getenv("JANUS_SERVICE_HOST") if os.getenv("JANUS_SERVICE_HOST") is not None else "localhost",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'path': os.getenv("JANUS_SERVICE_PATH") if os.getenv("JANUS_SERVICE_PATH") is not None else "/janus",
        'api_secret': os.getenv("JANUS_API_SECRET") if os.getenv("JANUS_API_SECRET") is not None else "janusrocks"
    }
    JANUS_STREAM_SETTINGS = {
        "server": os.getenv("JANUS_SERVICE_HOST") if os.getenv(
            "JANUS_SERVICE_HOST") is not None else "ec2-54-93-106-207.eu-central-1.compute.amazonaws.com",
        'port': os.getenv("JANUS_SERVICE_PORT") if os.getenv("JANUS_SERVICE_PORT") is not None else "8088",
        'ip': os.getenv("JANUS_SERVICE_IP") if os.getenv("JANUS_SERVICE_IP") is not None else "10.11.0.3",
        "schema": 'http'
    }

    MONGODB_SETTINGS = {
        'db': os.getenv("MONGODB_DATABASE_NAME") if os.getenv("MONGODB_DATABASE_NAME") is not None else 'streamingdb',
        'host': os.getenv("MONGODB_SERVICE_HOST") if os.getenv("MONGODB_SERVICE_HOST") is not None else 'localhost',
        'port': int(os.getenv("MONGODB_SERVICE_PORT")) if os.getenv("MONGODB_SERVICE_PORT") is not None else 27017
    }


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
