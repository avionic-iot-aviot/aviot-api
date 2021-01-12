from app.models import db
from app.models.device import Device

# todo terminare la configurazione del video room
videoroom_status = ('initializing', 'live', 'closed')


class VideoRoomInfo(db.Document):
    operator = db.StringField()  # TODO memorizzare l'id dell'operatore che ha creato il video room
    name = db.StringField(required=True)
    pin = db.StringField(required=True)
    secret = db.StringField(required=True)  # random secret per creare / distruggere la stanza
    server = db.StringField(required=True)
    label = db.StringField(default="")
    port = db.IntField()
    created_at = db.StringField(required=True)
    access_token = db.StringField(required=True)  # token utile per l'accesso ai servizio Janus
    status = db.StringField(default="", choices=videoroom_status)
    devices = db.ListField(db.ReferenceField(Device, default=None))
    deleted = db.BooleanField(default=False)

