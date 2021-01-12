from app.models import db
from app.models.organization import Organization

usr_role = ('admin', 'user', 'device-user', 'superadmin')  #FIXME togliere superadmin!!!
super_usr_role = ('super-device-user', 'super-admin')


class User(db.Document):
    login = db.StringField(required=True, unique=True)
    password = db.StringField(required=True)
    first_name = db.StringField(max_length=50)
    last_name = db.StringField(max_length=50)
    description = db.StringField(default="")
    role = db.StringField(
        required=True,
        choices=usr_role,
        default='user'
    )
    admin = db.BooleanField(default=False)
    organization = db.ReferenceField(Organization, default=None)


user = User({"name": "admin", "login": "admin", "password": "admin", "role": "superadmin", "admin": True})
print(user)