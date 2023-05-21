from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Room(db.Model):
    """ Room model """

    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key = True)
    room_name = db.Column(db.String(15), unique = True, nullable = False)
    host_username = db.Column(db.String(15), unique = False, nullable = False)
    opp_username = db.Column(db.String(15), unique = False, nullable = True)
    side = db.Column(db.String(5), unique = False, nullable = False)
    time_control = db.Column(db.Integer, unique = False, nullable = False)
    increment = db.Column(db.Integer, unique = False, nullable = False)
