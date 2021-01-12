from flask import request
from flask_restful import Resource
import app.models.streaming
import app.common.janus_api
from app.api.resources.schema import PhotoSchema, LabelPhotoModSchema
import random
import datetime
from flask_jwt_extended import jwt_required, current_user
from werkzeug.exceptions import BadRequest
from app import is_normal_user, is_admin


class PhotoEndpoint(Resource):

    @jwt_required
    @is_normal_user
    def get(self, photo_id):

        # role: admin, normal user
        photo_obj = app.models.streaming.Photo.objects(
            photo_id=photo_id,
            organization=current_user.organization
        ).first()

        if photo_obj is None or photo_obj.deleted is True:
            return {
                   'error': {
                       'id': 1,
                       'description': "photo id doesn't exist",
                       'details': {}
                    }
            }, 404  # photo doesn't not exits

        photo_schema = PhotoSchema()
        return photo_schema.dump(photo_obj, many=False)[0], 200

    @jwt_required
    @is_admin
    def delete(self, photo_id):

        # role: admin, normal user
        photo_obj = app.models.streaming.Photo.objects(
            photo_id=photo_id,
            organization=current_user.organization
        ).first()

        if photo_obj is None or photo_obj.deleted is True:
            return {
                   'error': {
                       'id': 1,
                       'description': "photo id doesn't exist",
                       'details': {}
                   }
            }, 404  # photo doesn't not exits

        photo_obj.deleted = True
        photo_obj.save()

        return None, 200

    @jwt_required
    @is_normal_user
    def put(self, photo_id):

        # role: admin, normal user
        # TODO controllare parametri

        photo_obj = app.models.streaming.Photo.objects(
            photo_id=photo_id,
            organization=current_user.organization
        ).first()

        if photo_obj is None or photo_obj.deleted is True:
            return {
                       'error': {
                           'id': 1,
                           'description': "photo id doesn't exist",
                           'details': {}
                       }
                   }, 404  # photo doesn't not exits

        try:

            json_data = request.get_json()

        except BadRequest:

            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': []
                       }
                   }, 400  # bad request

        photo_schema = LabelPhotoModSchema()
        data, errors = photo_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        label = data['label']
        photo_obj.label = label
        photo_obj.save()

        return None, 204  # No content

    @jwt_required
    @is_normal_user
    def post(self, stream_id):

        """
            1. generare uuid per lo screenshot
            2. rilevare il timestamp dello screenshot (rilevato durante l'attivazione della risorsa)
            3. rilevare eventuale label
            4. prendere la posizione gps dello screenshot dall'ultimo rilevato e memorizzato nella collezione StreamInfo
        """

        # role: admin, normal user
        stream_obj = app.models.streaming.StreamInfo.objects(
            s_id=int(stream_id),
            organization=current_user.organization
        ).first()

        if stream_obj is None or stream_obj.deleted is True:
            return {
                       'error': {
                           'id': 1,
                           'description': "stream id doesn't exist",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not exits

        if stream_obj.status != 'live':
            return {
                       'error': {
                           'id': 1,
                           'description': "stream has just stopped",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not exits

        date = datetime.datetime.utcnow()
        photo_id = random.getrandbits(32)
        photo_obj = app.models.streaming.Photo()
        photo_obj.date = date
        photo_obj.photo_id = photo_id
        photo_obj.status = 'processing'
        photo_obj.stream = stream_obj
        photo_obj.organization = current_user.organization
        photo_obj.save()

        return {
                   "photo_id": photo_id
               }, 201



