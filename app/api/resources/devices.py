from flask import request
from flask_restful import Resource
from app.api.resources.schema import DeviceSchema, StreamInfoSchema, DeviceStatusSchema
import app.models.device
import app.models.organization
import app.models.user
import app.models.streaming
from flask_jwt_extended import jwt_required, current_user, get_jwt_claims
from flask import current_app
from app import is_admin, is_normal_user, is_device_user


class DevicesEndpoint(Resource):

    @jwt_required
    @is_admin
    def post(self):

        # role: admin
        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        dev_schema = DeviceSchema()
        data, errors = dev_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        device_obj = app.models.device.Device.objects(
            name=data['name'],
            organization=current_user.organization
        ).first()

        if device_obj is not None:
            return {
                       'error': {
                           'id': 1,
                           'description': 'device exists',
                           'details': {}
                       }
                   }, 404  # Bad request

        dev = app.models.device.Device()
        dev.name = data['name']
        dev.description = data['description']
        dev.status = "offline"
        dev.organization = current_user.organization
        dev.save()

        return 201  # TODO controllare codice

    @jwt_required
    @is_normal_user
    def get(self, device_id=None):

        dev_schema = DeviceSchema()

        if device_id is None:
            devices = app.models.device.Device.objects(
                organization=current_user.organization
            )

            stream_live_list = {}
            for dev in devices:
                stream = app.models.streaming.StreamInfo.objects(
                    device_id=dev.id,
                    organization=current_user.organization,
                    status='live'
                ).first()

                stream_info_schema = StreamInfoSchema(exclude=['device_id'])
                if stream is not None:
                    stream_live_list[dev.name] = stream_info_schema.dump(stream)[0]

            return {
                'devices': dev_schema.dump(devices, many=True)[0],
                'live_streams': stream_live_list,
                'monitor': { #FIXME valutare utilizzo differente utente con ACL broker IMPOSTATO!
                    'host': current_app.config['MQTT_BROKER_SETTINGS']['hostname'],
                    'port': current_app.config['MQTT_BROKER_SETTINGS']['ws_port'],
                    'username': current_app.config['MQTT_BROKER_SETTINGS']['username'],
                    'password': current_app.config['MQTT_BROKER_SETTINGS']['password']
                }
            }
        else:
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

            #if device_obj.status == 'live':
            stream = app.models.streaming.StreamInfo.objects(
                device_id=device_obj,
                organization=current_user.organization,
                status='live'
            ).first()

            stream_info_schema = StreamInfoSchema(exclude=['device_id'])

            return {
                "device": dev_schema.dump(device_obj)[0],
                "live_stream": stream_info_schema.dump(stream)[0]
            }

    @jwt_required
    @is_device_user
    def put(self, device_id):

        # role: admin
        json_data = request.get_json()

        if not json_data:
            return {
                       'error': {
                           'id': 1,
                           'description': 'no input data provided or not json format',
                           'details': {}
                       }
                   }, 400  # Bad request

        dev_status_schema = DeviceStatusSchema()
        data, errors = dev_status_schema.load(json_data)

        if errors:
            return {
                       'error': {
                           'id': 2,
                           'description': 'validation error',
                           'details': errors
                       }
                   }, 422

        claims = get_jwt_claims()
        organization = None

        if "super-admin" in claims.keys():
            if claims['super-admin'] is True:
                if 'organization' not in data.keys():
                    return {
                               'error': {
                                   'id': 2,
                                   'description': 'validation error',
                                   'details': errors
                               }
                           }, 422

                if data['organization'] is not None:
                    organization = app.models.organization.Organization.objects(domain=data['organization']).first()

                    if organization is None:
                        return {
                                   'error': {
                                       'id': 2,
                                       'description': "organization doesn't not exist",
                                       'details': errors
                                   }
                               }, 422
        else:
            organization = current_user.organization

        device_obj = app.models.device.Device.objects(
                name=device_id,
                organization=organization
            ).first()

        device_obj.status = data['status']
        device_obj.save()

        return None, 204

