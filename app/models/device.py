from app.models import db
from app.models.organization import Organization

devices_status = ("streaming", "videoroom", "idle", "offline")


class Device(db.Document):
    name = db.StringField(required=True)
    description = db.StringField(default="")
    status = db.StringField(
        required=True,
        choices=devices_status,
        default="offline"
    )  # status of device
    organization = db.ReferenceField(Organization, required=True)


