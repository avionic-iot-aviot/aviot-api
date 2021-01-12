from flask import request
from flask_restful import Resource
from app.api.resources.schema import UserSchema, UserLoginSchema
import app.models.device
import app.models.organization
import app.models.user
import bcrypt
import datetime
from flask_jwt_extended import create_access_token, jwt_required, current_user
from app import is_admin, is_normal_user


class UsersEndpoint(Resource):

    @jwt_required
    @is_admin
    def post(self):

        # role: admin
        """
        #TODO fattorizzare
        if current_user.admin is not True:
            return {
                   'error': {
                       'id': 2,
                       'description': 'permission denied',
                       'details': ""
                   }
               }, 403
        """

        json_data = request.get_json()

        #TODO fattorizzare
        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        usr_schema = UserSchema()
        data, errors = usr_schema.load(json_data)

        # TODO fattorizzare
        if errors:
            return {
                   'error': {
                       'id': 2,
                       'description': 'validation error',
                       'details': errors
                   }
                }, 422

        org = app.models.organization.Organization.objects(
            domain=data['organization_domain']
        ).first()

        # TODO fattorizzare
        if org is None:
            return {
               'error': {
                   'id': 1,
                   'description': "organization doesn't exists",
                   'details': {}
               }
            }, 404  # Organization doesn't not ex

        # check if the user login with the same organization is in the db
        usr = app.models.user.User.objects(
            login=data['login'],
            organization=current_user.organization
        ).first()

        if usr is not None:
            return {
                   'error': {
                       'id': 1,
                       'description': "user exists",
                       'details': {}
                   }
               }, 404  # User exists

        usr = app.models.user.User()
        usr.login = data['login']
        salt = bcrypt.gensalt()
        password = data['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, salt)
        usr.password = str(hashed_password, 'utf-8')
        usr.first_name = data['first_name']
        usr.last_name = data['last_name']
        usr.description = data['description']
        usr.organization = org
        usr.role = data['role']
        usr.save()

        return 201

    @jwt_required
    @is_normal_user
    def get(self):

        user_schema = UserSchema()

        return user_schema.dump(current_user)


class UserAuthEndpoint(Resource):

    def post(self):

        login_schema = UserLoginSchema()
        json_data = request.get_json()

        if not json_data:
            return {
                   'error': {
                       'id': 1,
                       'description': 'no input data provided or not json format',
                       'details': {}
                   }
               }, 400  # Bad request

        data, errors = login_schema.load(json_data)
        if errors:
            return {
                   'error': {
                       'id': 2,
                       'description': 'validation error',
                       'details': errors
                   }
               }, 422

        login = data['login']
        password = data['password']
        user = app.models.user.User.objects(login=login).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) is True:
            user_claims = None

            if user.role == 'super-admin':
                user_claims = {"super-admin": True}

            return {
                'access_token': create_access_token(
                    identity=login,
                    user_claims=user_claims,
                    expires_delta=datetime.timedelta(hours=1)
                )
            }
        else:
            return {
               'error': {
                   'id': 4,
                   'description': 'login or password not valid',
                   'details': {}
               }
           }, 422  # Bad request


class SuperUserAuthEndpoint(Resource):

    def post(self):

        login_schema = UserLoginSchema()
        json_data = request.get_json()

        if not json_data:
            return {
                   'error': {
                       'id': 1,
                       'description': 'no input data provided or not json format',
                       'details': {}
                   }
               }, 400  # Bad request

        data, errors = login_schema.load(json_data)
        if errors:
            return {
                   'error': {
                       'id': 2,
                       'description': 'validation error',
                       'details': errors
                   }
               }, 422

        login = data['login']
        password = data['password']
        user = app.models.user.SuperUser.objects(login=login).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) is True:
            return {
                'access_token': create_access_token(
                    identity=login,
                    user_claims={'super-admin': True},
                    expires_delta=datetime.timedelta(hours=1)
                )
            }
        else:
            return {
               'error': {
                   'id': 4,
                   'description': 'login or password not valid',
                   'details': {}
               }
           }, 422  # Bad request
