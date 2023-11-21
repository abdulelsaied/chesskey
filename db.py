from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Rooms(db.Model):
    """ Rooms model """

    __tablename__ = "rooms"
    room = db.Column(db.String(4), primary_key = True, unique = True, nullable = False)
    user1 = db.Column(db.String(15), unique = False, nullable = False)
    user2 = db.Column(db.String(15), unique = False, nullable = True)

class RoomInfo(db.Model):
    """ RoomIinfo model"""

    __tablename__ = "roominfo"
    room = db.Column(db.String(4), primary_key = True, unique = True, nullable = False)
    user1_side = db.Column(db.String(5), unique = False, nullable = False)
    user2_side = db.Column(db.String(5), unique = False, nullable = False)
    time_control = db.Column(db.Integer, unique = False, nullable = False)
    increment = db.Column(db.Integer, unique = False, nullable = False)

class Connection(db.Model):
    """ Connection model """
    __tablename__ = "connection"
    room = db.Column(db.String(4), primary_key = True, unique = True, nullable = False)
    user1_connect = db.Column(db.Boolean, unique = False, nullable = False)
    user2_connect = db.Column(db.Boolean, unique = False, nullable = False)
    live = db.Column(db.String(4), unique = False, nullable = False)
    ## ADD FLAG FOR WINNER AND REASON OF LAST GAME ENDING

class GameInfo(db.Model):
    __tablename__ = "gameinfo"
    room = db.Column(db.String(4), primary_key = True, unique = True, nullable = False)
    fen = db.Column(db.Text, unique = False, nullable = False)
    move_log = db.Column(db.Text, unique = False, nullable = False)
    user1_last_move = db.Column(db.TIMESTAMP, unique = False, nullable = True)
    user2_last_move = db.Column(db.TIMESTAMP, unique = False, nullable = True)
    user1_time_left = db.Column(db.Interval, unique = False, nullable = True)
    user2_time_left = db.Column(db.Interval, unique = False, nullable = True)
    user1_score = db.Column(db.Float, unique = False, nullable = False)
    user2_score = db.Column(db.Float, unique = False, nullable = False)