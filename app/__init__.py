from flask import Flask, g, abort
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
import functools
from flask_jwt_extended import jwt_required, current_user

db = MongoEngine()
jwt = JWTManager()
cors = CORS()


# check if user has admin role
def is_admin(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# check if user has user role
def is_normal_user(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role not in ('user', 'admin', 'super-admin'):
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# check if user has device role
def is_device_user(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role not in ('super-admin', 'device-user'):
            abort(403)
        return f(*args, **kwargs)
    return wrapped


@jwt.user_loader_callback_loader
def get_usr_obj(identity):
    import app.models.user

    usr_obj = app.models.user.User.objects(login=identity).first()
    # TODO define a custom error message if usr_obj is None
    return usr_obj


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)

    # Rest API app
    from .api import device_streaming_api
    app.register_blueprint(
        device_streaming_api,
        url_prefix="/api/v1.0"
    )

    # Web App
    from .web import webapp
    app.register_blueprint(webapp)

    return app
