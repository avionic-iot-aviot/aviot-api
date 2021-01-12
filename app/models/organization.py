import datetime
from app.models import db


class Organization(db.Document):
    domain = db.StringField(required=True, unique=True)
    name = db.StringField(required=True)
    description = db.StringField(default="")
    created_at = db.DateTimeField(default=datetime.datetime.now)

