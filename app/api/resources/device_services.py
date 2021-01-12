from flask import request
from flask_restful import Resource
import app.models.streaming
import app.common.janus_api
from app.api.resources.schema import StartStreamSchema
import json
import app.models.videoroom
from flask import current_app
import random
import time
from flask_jwt_extended import jwt_required, current_user
import app.models.device
import app.models.user
from app import is_normal_user


class DeviceServicesEndpoint(Resource):

    @jwt_required
    @is_normal_user
    def post(self, device_id, op):

        # role: admin, normal user
        device_obj = app.models.device.Device.objects(
            name=device_id,
            organization=current_user.organization
        ).first()

        if device_obj is None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'device id error',
                           'details': {}
                       }
                   }, 400  # Bad request

        try:

            if op == "start-streaming":

                json_data = request.get_json()
                start_stream_schema = StartStreamSchema()
                data, errors = start_stream_schema.load(json_data)

                if errors:
                    return {
                               'error': {
                                   'id': 2,
                                   'description': 'validation error',
                                   'details': errors
                               }
                           }, 422

                # check devices status
                if device_obj.status != 'idle' and data['force_start'] is False:
                    return {
                               'error': {
                                   'id': 1,
                                   'description': 'device busy',
                                   'details': {}
                               }
                           }, 400  # Bad request


                video_port = None
                audio_port = None
                streaming_server_ip = None
                streaming_server_port = None
                janus_feed_id = None

                # 1. create streaming endpoint (fattorizzare la funzione di creazione dello stream)
                if data['create_endpoint'] is True:
                    # A. Richiesta a Janus per lo stream

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
                        name_feed=device_id,
                        id_feed=janus_feed_id,
                        description=device_id,  # TODO verificare il contenuto, memorizzare SERIAL su DB
                        pin=janus_feed_pin,
                        audio_enabled=data['audio'],
                        is_private=True,
                        permanent=True,
                        session=janus_session)

                    app.common.janus_api.streaming_recording(
                        token=janus_token,
                        transaction=janus_transaction,
                        streaming_id=janus_feed_id,
                        state="enable",
                        session=janus_session
                    )

                    video_port = response['plugindata']['data']['stream']['video_port']  # TODO store in DB
                    audio_port = response['plugindata']['data']['stream']['audio_port'] if data['audio'] else 0
                    streaming_server_schema = current_app.config['JANUS_STREAM_SETTINGS']['schema']
                    streaming_server_ip = current_app.config['JANUS_STREAM_SETTINGS']['server']
                    streaming_server_port = current_app.config['JANUS_STREAM_SETTINGS']['port']

                    stream_info = app.models.streaming.StreamInfo()
                    stream_info.device_id = device_obj
                    stream_info.label = data['label']
                    stream_info.s_id = janus_feed_id
                    stream_info.status = 'live'
                    stream_info.ts = str(time.time())
                    stream_info.s_pin = janus_feed_pin
                    stream_info.s_token = janus_token
                    stream_info.server_ip = streaming_server_ip
                    stream_info.server_port = streaming_server_port
                    stream_info.server_schema = streaming_server_schema
                    stream_info.organization = current_user.organization
                    stream_info.save()

                # B. communication with device
                if data['create_endpoint'] is True:
                    return {
                               "janus_token": janus_token,
                               "janus_feed_id": janus_feed_id,
                               "janus_feed_pin": janus_feed_pin,
                               "streaming_server_schema": streaming_server_schema,
                               "streaming_server_ip": streaming_server_ip,
                               "streaming_server_port": streaming_server_port
                       }, 201
                else:
                    return None, 200,

            if op == "stop-streaming":

                json_data = request.get_json()  #FIXME controllare i dati

                # communication with drone

                return None, 200  # todo da verificare

            if op == "stop-videoroom":

                json_data = request.get_json()
                if not json_data:
                    return {
                               'error': {
                                   'id': 1,
                                   'description': 'no videoroom name on request',
                                   'details': {}
                               }
                           }, 400  # Bad request

                data = json_data
                videoroom_name = str(data['videoroom_name'])

                # get videoroom info
                videoroom_obj = app.models.videoroom.VideoRoomInfo.objects(name=videoroom_name).first()

                if videoroom_obj is None or videoroom_obj.deleted is True:
                    return {
                               'error': {
                                   'id': 1,
                                   'description': "videoroom name doesn't exists",
                                   'details': {}
                               }
                           }, 404  # videoroom doesn't not exits

                # check if the device is the last streamer on the videoroom
                devices_in_vr = [(d.name, d.status) for d in videoroom_obj.devices if d.name != device_id]
                check_if_last = True

                if len(devices_in_vr) > 0:
                    for d in devices_in_vr:
                        if d[0] == 'videoroom':
                            check_if_last = False

                if check_if_last:
                    videoroom_obj.status = 'closed'
                    videoroom_obj.save()

                # communication with drone

                return None, 200  # todo da verificare

            if op == "start-videoroom":

                # TODO check devices status
                json_data = request.get_json()
                if not json_data:

                    return {
                               'error': {
                                   'id': 1,
                                   'description': 'no videoroom name on request',
                                   'details': {}
                               }
                           }, 400  # Bad request

                data = json_data
                videoroom_name = str(data['videoroom_name'])

                # get videoroom info
                videoroom_obj = app.models.videoroom.VideoRoomInfo.objects(name=videoroom_name).first()

                if videoroom_obj is None or videoroom_obj.deleted is True:
                    return {
                               'error': {
                                   'id': 1,
                                   'description': "videoroom name doesn't exists",
                                   'details': {}
                               }
                           }, 404  # videoroom doesn't not exits

                videoroom_obj.status = 'live'
                videoroom_obj.save()

                # communication with drone
        except:
            return None, 400
        else:
            return None, 200




