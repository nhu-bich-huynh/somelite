from database import Db
from app import db


class User:
    def __init__(self, id, name, email=None, password=None, age=None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.age = age

    def get(user_id):
        user = db.get_user(user_id)

        if not user:
            return None

        return User(user[0], user[1].capitalize(), user[2], user[3], user[4])

    @property
    def is_authenticated(self):
        return self.is_active

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
