from marshmallow import Schema, fields, validate
from app.models.user import usr_role
from app.models.device import devices_status


class PositionSchema(Schema):
    type = fields.String()
    coordinates = fields.List(fields.List(fields.Integer))


class TrackingSchema(Schema):
    l_date = fields.List(fields.DateTime, required=True)
    steps = fields.Nested(PositionSchema(only=('coordinates',)))


class DeviceStatusSchema(Schema):
    status = fields.String(
        required=True,
        validate=validate.OneOf(devices_status)
    )
    organization = fields.String()

# TODO da rivedere organizzazione classi
class DeviceSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)
    status = fields.String(dump_only=True, default='offline')


class StreamInfoSchema(Schema):
    s_id = fields.Integer(
        required=True,
        dump_only=True
    )

    s_pin = fields.Integer(
        required=True,
        dump_only=True
    )

    s_token = fields.String(
        required=True,
        dump_only=True
    )

    device_id = fields.Nested(DeviceSchema)

    date_start = fields.DateTime(
        required=True,
        dump_only=True
    )

    date_stop = fields.DateTime(
        required=True,
        dump_only=True
    )

    label = fields.String(
        required=True,
        dump_only=True
    )

    status = fields.String(
        required=True,
        dump_only=True
    )

    url = fields.String(
        required=True,
        dump_only=True
    )

    server_ip = fields.String(
        required=True,
        dump_only=True
    )

    server_port = fields.Integer(
        required=True,
        dump_only=True
    )

    server_schema = fields.String(
        required=True,
        dump_only=True
    )

    tracking = fields.Nested(TrackingSchema)


class StreamingEndpointSchema(Schema):
    serial = fields.String(required=True)
    label = fields.String(default='')
    audio = fields.Boolean(default=False)  # se lo streaming trasporta pure l'audio


class PhotoSchema(Schema):
    # stream = db.ReferenceField('StreamInfo')
    photo_id = fields.Integer(required=True)  # photo id
    label = fields.String(required=True)
    date = fields.DateTime()
    url = fields.String()  # path of image stored and post-processed
    pos = fields.Nested(PositionSchema(only=('coordinates',)))
    status = fields.String(required=True)  # status of photo processing


class VideosSearch(Schema):
    from_date = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    to_date = fields.DateTime(format="%Y-%m-%d %H:%M:%S")
    label = fields.String()
    coordinates = fields.List(fields.Nested(PositionSchema))  # must be three coordinates at least


class CreateVideoroomSchema(Schema):
    label = fields.String()


class VideoroomSchema(Schema):
    name = fields.String(required=True, dump_only=True)
    pin = fields.String(required=True, dump_only=True)
    secret = fields.String(required=True, dump_only=True)
    label = fields.String(required=True, dump_only=True)
    server = fields.String(required=True, dump_only=True)
    port = fields.Integer(required=True, dump_only=True)
    created_at = fields.String(required=True, dump_only=True)
    status = fields.String(required=True, dump_only=True)
    access_token = fields.String(required=True, dump_only=True)
    devices = fields.List(fields.Nested(DeviceSchema))


class DeviceIDSchema(Schema):
    name = fields.String(required=True)


class DevicesIDListSchema(Schema):
    devices = fields.List(fields.Nested(DeviceIDSchema))


class StartStreamSchema(Schema):
    audio = fields.Boolean(required=True)
    label = fields.String(default='')
    create_endpoint = fields.Boolean(missing=False)
    force_start = fields.Boolean(missing=False)


class OrganizationSchema(Schema):
    domain = fields.String(required=True)
    name = fields.String(required=True)
    description = fields.String()


class UserSchema(Schema):
    login = fields.String(required=True)
    password = fields.String(required=True, load_only=True)  # controllare la lunghezza e la difficolta' della password
    first_name = fields.String(max_length=50)
    last_name = fields.String(max_length=50)
    description = fields.String(default="")
    role = fields.String(validate=validate.OneOf(usr_role))
    organization_domain = fields.String(required=True)


class UserLoginSchema(Schema):
    login = fields.String(required=True)
    password = fields.String(required=True)


class LabelPhotoModSchema(Schema):
    label = fields.String(required=True)

