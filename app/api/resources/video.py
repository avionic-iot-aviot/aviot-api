from flask import request
from flask_restful import Resource
import app.models.streaming
import app.common.janus_api
from app.api.resources.schema import PhotoSchema, LabelPhotoModSchema
import random
import datetime
from flask_jwt_extended import jwt_required, current_user
from werkzeug.exceptions import BadRequest
from app import is_admin, is_normal_user


class VideoEndpoint(Resource):

    @jwt_required
    @is_admin
    def delete(self, stream_id):

        # role: admin
        if stream_id is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'you must provide a serial number',
                           'details': {}
                       }
                   }, 400  # Bad request

        stream_obj = app.models.streaming.StreamInfo.objects(
            s_id=stream_id,
            deleted=False,
            status="stored",
            organization=current_user.organization
        ).first()

        if stream_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': "video doesn't exist",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not exits

        stream_obj.deleted = True
        stream_obj.save()

        return None, 200

