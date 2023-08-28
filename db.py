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
    user2_side = db.Column(db.String(5), unique = False, nullable = False)
    time_control = db.Column(db.Integer, unique = False, nullable = False)
    increment = db.Column(db.Integer, unique = False, nullable = False)
    user1_connect = db.Column(db.Boolean, unique = False, nullable = False)
    user2_connect = db.Column(db.Boolean, unique = False, nullable = False)
    live = db.Column(db.Boolean, unique = False, nullable = False)
    fen = db.Column(db.Text, unique = False, nullable = False)
    move_log = db.Column(db.Text, unique = False, nullable = False)
    user1_last_move = db.Column(db.TIMESTAMP, unique = False, nullable = True)
    user2_last_move = db.Column(db.TIMESTAMP, unique = False, nullable = True)
    user1_time_left = db.Column(db.Interval, unique = False, nullable = True)
    user2_time_left = db.Column(db.Interval, unique = False, nullable = True)


