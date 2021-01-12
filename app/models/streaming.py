from app.models import db
import datetime
from app.models.device import Device
from app.models.organization import  Organization

stream_status = ('live', 'processing', 'stored')
photo_status = ('processing', 'available')


class Tracking(db.EmbeddedDocument):
    l_date = db.ListField(db.DateTimeField(), required=True)  # time instant of gps coordinates
    steps = db.MultiPointField()


class StreamInfo(db.Document):
    s_id = db.IntField(required=True)  # stream id
    device_id = db.ReferenceField('Device')  # serial
    organization = db.ReferenceField('Organization', default=None)  # It is correct?
    s_pin = db.IntField(required=True)  # stream pin
    s_token = db.StringField(required=True)  # stream token for janus
    date_start = db.DateTimeField(default=datetime.datetime.utcnow)
    date_stop = db.DateTimeField()
    label = db.StringField(default="")  # label
    status = db.StringField(required=True, choices=stream_status)  # status of live streaming
    url = db.StringField()  # path of video stored and post-processed
    tracking = db.EmbeddedDocumentField(Tracking, default=None)  # gps tracking
    server_ip = db.StringField(required=True)  # server ip janus
    server_port = db.IntField(required=True)  # server port janus
    server_schema = db.StringField(required=True, default='http')
    deleted = db.BooleanField(default=False)

    # For ignoring this error when having extra fields while data
    # loading, set strict to False in your meta dictionary.
    meta = {'strict': False}


class Photo(db.Document):
    stream = db.ReferenceField('StreamInfo')
    organization = db.ReferenceField('Organization')  # It is correct?
    photo_id = db.IntField(required=True)  # photo id
    date = db.DateTimeField(required=True)  # screenshot timestamp
    label = db.StringField(default="")
    url = db.StringField()  # path of image stored and post-processed
    pos = db.PointField()
    status = db.StringField(required=True, choices=photo_status)  # status of photo processing
    deleted = db.BooleanField(default=False)

    meta = {'strict': False}
