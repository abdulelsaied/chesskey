from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Room(db.Model):
    """ Room model """

    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key = True)
    room = db.Column(db.String(15), unique = True, nullable = False)
    user1 = db.Column(db.String(15), unique = False, nullable = False)
    user2 = db.Column(db.String(15), unique = False, nullable = True)
    user1_side = db.Column(db.String(5), unique = False, nullable = False)
    time_control = db.Column(db.Integer, unique = False, nullable = False)
    increment = db.Column(db.Integer, unique = False, nullable = False)
    user1_disconnect = db.Column(db.Boolean, unique = False, nullable = False)
    user2_disconnect = db.Column(db.Boolean, unique = False, nullable = False)
