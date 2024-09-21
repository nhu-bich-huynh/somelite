from app import db


class Post:
    def __init__(self, id, user_id, date, message):
        self.id = id
        self.user_id = user_id
        self.date = date.strftime("%H.%M, %A %d, %B")
        self.message = message

        return

    @property
    def likes(self):
        return db.show_all_likes(self.id)
