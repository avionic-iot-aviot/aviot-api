from flask import request
from flask_restful import Resource
from flask import current_app
import app.models.streaming
import app.models.device
from app.api.resources.schema import StreamingEndpointSchema,  StreamInfoSchema
import app.common.janus_api
import random
import time
import datetime
from flask_jwt_extended import jwt_required, current_user, get_jwt_claims
from werkzeug.exceptions import BadRequest
from app import is_normal_user, is_admin, is_device_user


class StreamingEndpoint(Resource):

    #@jwt_required
    #@is_device_user
    def post(self):

        # role: device-user (when device must create streaming endpoint)
        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        #print(json_data)

        se_schema = StreamingEndpointSchema()
        data, errors = se_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422


        # 1. Richiesta a Janus per lo stream

        # creo una sola volta lo janus token
        janus_token = app.common.janus_api.get_janus_token(
            'janus',
            [
                'janus.plugin.streaming',
            ],
            24 * 60 * 60 * 365
        )

        janus_transaction = app.common.janus_api.get_transaction_id()
        janus_session = app.common.janus_api.create_session(
            janus_token,
            janus_transaction,
            'janus.plugin.streaming'
        )
        janus_feed_id = random.getrandbits(32)
        janus_feed_pin = random.getrandbits(16)
        response = app.common.janus_api.create_feed(
            token=janus_token,
            transaction=janus_transaction,
            name_feed=data['serial'],
            id_feed=janus_feed_id,
            description=data['serial'],
            pin=janus_feed_pin,
            audio_enabled=data['audio'],
            is_private=False,
            permanent=True,
            session=janus_session)

        # MIK - disable streaming_recording
        #app.common.janus_api.streaming_recording(
        #    token=janus_token,
        #    transaction=janus_transaction,
        #    streaming_id=janus_feed_id,
        #    state="enable",
        #    session=janus_session
        #)

        video_port = response['plugindata']['data']['stream']['video_port']  # TODO store in DB
        audio_port = response['plugindata']['data']['stream']['audio_port'] if data['audio'] else 0
        streaming_server_schema = current_app.config['JANUS_STREAM_SETTINGS']['schema']
        streaming_server_ip = current_app.config['JANUS_STREAM_SETTINGS']['ip']
        streaming_server_port = current_app.config['JANUS_STREAM_SETTINGS']['port']

        # MIK - disable mongo interactions
        stream_info = app.models.streaming.StreamInfo()
        #stream_info.device_id = device_obj
        #stream_info.label = data['label']
        stream_info.s_id = janus_feed_id
        stream_info.status = 'live'
        stream_info.ts = str(time.time())
        stream_info.s_pin = janus_feed_pin
        stream_info.s_token = janus_token
        stream_info.server_ip = streaming_server_ip
        stream_info.server_port = streaming_server_port
        stream_info.server_schema = streaming_server_schema
        #stream_info.organization = current_user.orgarnization

        stream_info.save()

        # 5. Ritornare al client le info sullo stream
        return {
            "janus_token": janus_token,
            "video_port": video_port,
            "audio_port": audio_port,
            "janus_feed_id": janus_feed_id,
            "janus_feed_pin": janus_feed_pin,
            "streaming_server_ip": streaming_server_ip,
            "streaming_server_port": streaming_server_port
        }, 201

    @jwt_required
    @is_normal_user
    def get(self, stream_id):

        # role: admin, normal user
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
            organization=current_user.organization
        ).first()

        if stream_obj is None or stream_obj.deleted is True:
            return {
                       'error': {
                           'id': 1,
                           'description': "stream id doesn't exists",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not exits

        stream_schema = StreamInfoSchema()

        return stream_schema.dump(stream_obj)[0], 200

    #@jwt_required
    #@is_device_user
    def delete(self, stream_id, organization_d=None):

        # role: device-user
        if stream_id is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'you must provide a serial number',
                           'details': {}
                       }
                   }, 400  # Bad request
        stream_obj = app.models.streaming.StreamInfo.objects(
            s_id=stream_id
        ).first()

        if stream_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': "stream id doesn't exists",
                           'details': {}
                       }
                   }, 404  # Stream doesn't not exits

        # update stream status
        stream_obj.status = 'processing'
        stream_obj.date_stop = datetime.datetime.utcnow()
        stream_obj.save()

        janus_token = app.common.janus_api.get_janus_token(
            'janus',
            [
                'janus.plugin.streaming',
                'janus.plugin.videoroom'
            ],
            24 * 60 * 60 * 365
        )

        janus_transaction = app.common.janus_api.get_transaction_id()
        janus_session = app.common.janus_api.create_session(
            janus_token,
            janus_transaction,
            'janus.plugin.streaming'
        )

        app.common.janus_api.streaming_recording(
            token=janus_token,
            transaction=janus_transaction,
            streaming_id=int(stream_id),
            state="disabled",
            session=janus_session
        )

        app.common.janus_api.destroy_feed(
            janus_token,
            janus_transaction,
            int(stream_id),
            janus_session
        )
        return None, 200

    @jwt_required
    @is_normal_user
    def put(self, stream_id):

        # role: admin, normal user
        try:

            json_data = request.get_json()
            claims = get_jwt_claims()

        except BadRequest:

            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': []
                       }
                   }, 400  # bad request

        if stream_id is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'you must provide a stream_id',
                           'details': {}
                       }
                   }, 400  # Bad request

        claims = get_jwt_claims()
        if "super-admin" in claims.keys():
            if claims['super-admin'] is True:
                if 'organization' not in json_data.keys():
                    return {
                               'error': {
                                   'id': 2,
                                   'description': 'validation error',
                                   'details': {}
                               }
                           }, 422

                organization = app.models.organization.Organization.objects(domain=json_data['organization']).first()
                if organization is None:
                    return {
                               'error': {
                                   'id': 2,
                                   'description': "organization doesn't not exist",
                                   'details': {}
                               }
                           }, 422
        else:
            organization = current_user.organization

        stream_obj = app.models.streaming.StreamInfo.objects(
            s_id=stream_id,
            organization=organization
        ).first()

        if stream_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': "stream id doesn't exist",
                           'details': {}
                       }
                   }, 404  # stream doesn't not exit

        label_check = False
        pos_check = False
        if 'label' in json_data:
            label = json_data['label']
            stream_obj.label = label
            label_check = True

        # check if gps data is set in json data and the user is super-admin...
        if 'pos' in json_data and claims.get('super-admin', False) is True:
            pos_check = True
            if stream_obj.status == 'live':
                if stream_obj.tracking is None:
                    stream_obj.tracking = app.models.streaming.Tracking()

                stream_obj.tracking.l_date.append(json_data['pos']['ts'])

                prev_steps = stream_obj.tracking.steps
                long = json_data['pos']['long']
                lat = json_data['pos']['lat']
                if long is not None and lat is not None:

                    if prev_steps is None and long is not None and lat is not None:
                        stream_obj.tracking.steps = [[float(json_data['pos']['long']), float(json_data['pos']['lat'])]]
                    else:
                        # I have to force unset field, otherwise the coordinates values doesn't not updated!
                        # check index!!
                        # db.StreamInfo.objects(s_id=payload['stream_id']).update(unset__tracking__steps=1)
                        prev_steps['coordinates'].append(
                            [float(json_data['pos']['long']), float(json_data['pos']['lat'])]
                        )
                        stream_obj.tracking.steps = prev_steps['coordinates']

        if label_check is False and pos_check is False:
            return {
                   'error': {
                       'id': 2,
                       'description': 'validation error',
                       'details': []
                   }
               }, 422

        stream_obj.save()

        return None, 204  # No content
