from flask import request
from flask_restful import Resource
from flask import current_app
import app.models.videoroom
import app.models.device
from app.api.resources.schema import VideoroomSchema, DevicesIDListSchema, CreateVideoroomSchema
import app.common.janus_api
import random
import time
from flask_jwt_extended import jwt_required, current_user
from app import is_normal_user, is_admin


class VideoroomEndpoint(Resource):
    #@jwt_required
    #@is_normal_user
    def post(self):

        # role: admin, normal user
        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        cvr_schema = CreateVideoroomSchema()
        data, errors = cvr_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        # 1. Richiesta a Janus per la creazione di una nuova video room

        # creo una sola volta lo janus token
        janus_token = app.common.janus_api.get_janus_token(
            'janus',
            [
                'janus.plugin.videoroom'
            ],
            24 * 60 * 60 * 365
        )

        janus_transaction = app.common.janus_api.get_transaction_id()
        janus_session = app.common.janus_api.create_session(
            janus_token,
            janus_transaction,
            'janus.plugin.videoroom'
        )
        videoroom_name = random.getrandbits(16)

        _, videoroom_pin, videoroom_secret = app.common.janus_api.create_videoroom(
            token=janus_token,
            transaction=janus_transaction,
            description="description",  # TODO inserire descrizione
            vr_name=videoroom_name,
            is_private=True,
            permanent=True,
            session=janus_session
        )


        # TODO controllare i parametri
        streaming_server_ip = current_app.config['JANUS_STREAM_SETTINGS']['server']
        streaming_server_port = current_app.config['JANUS_STREAM_SETTINGS']['port']

        videoroom = app.models.videoroom.VideoRoomInfo()
        videoroom.status = "initializing"
        videoroom.created_at = str(time.time())
        videoroom.name = str(videoroom_name)
        videoroom.label = data['label']
        videoroom.pin = str(videoroom_pin)
        videoroom.secret = videoroom_secret
        videoroom.server = streaming_server_ip
        # FIXME in realta' la porta potrebbe non essere necessaria se e' presente un reverse-proxy (es. nginx)
        videoroom.port = streaming_server_port
        videoroom.access_token = janus_token
        videoroom.save()

        # 5. Ritornare al client le info sul videoroom creato
        return {
            "janus_token": janus_token,
            "videoroom_name": videoroom_name,
            "videoroom_pin": videoroom_pin,
            "videoroom_secret": videoroom_secret,
            "streaming_server_ip": streaming_server_ip,
            "streaming_server_port": streaming_server_port
        }, 201

    @jwt_required
    @is_normal_user
    def get(self, videoroom_name=None):

        # role: admin, normal user
        vr_schema = VideoroomSchema()
        if videoroom_name is None:
            videorooms = app.models.videoroom.VideoRoomInfo.objects(deleted=False)
            return vr_schema.dump(videorooms, many=True)

        else:

            videoroom = app.models.videoroom.VideoRoomInfo.objects(
                name=videoroom_name,
                deleted=False
            ).first()

            if videoroom is None or videoroom.deleted is True:
                return {
                       'error': {
                           'id': 1,
                           'description': "videroom doesn't exists",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not ex

            return vr_schema.dump(videoroom)

    #@jwt_required
    #@is_admin
    def delete(self, videoroom_name):

        if videoroom_name is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'you must provide a videoroom_name',
                           'details': {}
                       }
                   }, 400  # Bad request

        videoroom_obj = app.models.videoroom.VideoRoomInfo.objects(name=videoroom_name).first()

        if videoroom_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': "videoroom doesn't exists",
                           'details': {}
                       }
                   }, 404  # Videoroom doesn't not exits

        # update stream status
        videoroom_obj.deleted = True
        videoroom_obj.status = 'closed'
        videoroom_obj.save()

        janus_token = app.common.janus_api.get_janus_token(
            'janus',
            [
                'janus.plugin.videoroom'
            ],
            24 * 60 * 60 * 365
        )

        janus_transaction = app.common.janus_api.get_transaction_id()
        janus_session = app.common.janus_api.create_session(
            janus_token,
            janus_transaction,
            'janus.plugin.videoroom'
        )

        app.common.janus_api.destroy_videoroom(
            token=janus_token,
            transaction=janus_transaction,
            vr_name=int(videoroom_name),
            secret=videoroom_obj.secret,
            permanent=True,
            session=janus_session
        )

        return 200

    @jwt_required
    @is_normal_user
    def put(self, videoroom_name):

        if videoroom_name is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'you must provide a videoroom_name',
                           'details': {}
                       }
                   }, 400  # Bad request

        videoroom_obj = app.models.videoroom.VideoRoomInfo.objects(name=videoroom_name).first()

        if videoroom_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': "videoroom doesn't exists",
                           'details': {}
                       }
                   }, 404  # Videoroom doesn't not exits

        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        dl_schema = DevicesIDListSchema()
        data, errors = dl_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        dev_list = []
        for d in data['devices']:
            device = app.models.device.Device.objects(name=d["name"]).first()
            if device is not None:  # check if device exists
                dev_list.append(device)

        videoroom_obj.devices = dev_list
        videoroom_obj.save()

        return 201  # TODO controllare


