import os
import random
import time
import json
import linecache
from datetime import timedelta, datetime
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_socketio import SocketIO, send, join_room, leave_room
from db import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}  
db = SQLAlchemy(app)
sio = SocketIO(app)

##########
# ROUTES #
##########

@app.route("/", methods = ['GET', 'POST'])
def index():
    """
    routes the user to the landing page.
    POST requests from forms are handled, or index with possible alert message is rendered

    :return: None
    """
    if request.method == 'POST':
        session.clear()
        if 'createSubmit' in request.form:
            session['room'] = generate_key()
            session['username'] = request.form.get("username")
            user1_side = random.choice(["white", "black"]) if request.form.get("side") == "random" else request.form.get("side")
            print(user1_side)
            room = Rooms(
                room = session['room'],
                user1 = session['username'],
                user2 = None
            )
            roominfo = RoomInfo(
                room = session['room'],
                user1_side = user1_side,
                user2_side = flip_side(user1_side),
                time_control = request.form.get("time_control"),
                increment = request.form.get("increment")
            )
            db.session.add(room)
            db.session.add(roominfo)
            db.session.commit()
            return redirect(url_for("create_room", room = session['room'])) 
        elif 'joinSubmit' in request.form:
            room_key = request.form.get("room")
            room_row = db.session.query(Rooms).filter_by(room = room_key).first()
            if not room_row or (room_row.user1 and room_row.user2):
                return render_template("index.html")
            session['room'] = room_key
            session['username'] = request.form.get("username") 
            if session['username'] == room_row.user1:
                if len(session['username']) == 15:
                    session['username'] = session['username'][:-1]        
                session['username'] += "1"  
            room_row.user2 = session['username']
            db.session.commit()
            return redirect(url_for("create_room", room = session['room']))
    else:
        session.clear()
        return render_template("landing.html")

@app.route("/<room>", methods = ['GET', 'POST'])
def create_room(room):
    """
    creates a room and routes the user to that lobby.

    :param lobby: unique string for a chess lobby
    :return: None
    """
    if room == "favicon.ico":
        return redirect(url_for("index"))
    room_row = db.session.query(Rooms).filter_by(room = room).first()
    if not room_row:
        print("Lobby" + room + "does not exist")
        return redirect(url_for("index"))
    if request.method == 'POST' and "usernameSubmit" in request.form:
        ### THIS IS WHERE SHOULD CHANGE STATE OF THE GAME 
        session['room'] = room
        session['username'] = request.form.get("username")
        room_row.user2 = session['username']
        db.session.commit()
        return render_template("game.html", data = session)
    if session.get("username") and (session.get("username") == room_row.user1 or session.get("username") == room_row.user2):
        session['room'] = room_row.room
        return render_template("game.html", data = session)
    if not room_row.user2:
        return render_template("username.html")
    print("lobby" + room + "is full!")
    return redirect(url_for("index"))

###################
# SOCKETIO EVENTS #
###################

@sio.on("connect", namespace = "/chat")
def connect():
    """
    triggered when client connects to chat socket

    :return: None
    """
    print(request.sid, ' connected to chat')

@sio.on("connect", namespace = "/game")
def connect():
    """
    triggered when client connects to game socket

    :return: None
    """
    print(request.sid, ' connected to game')

@sio.on("chat_msg", namespace = "/chat")
def chat_msg(msg):
    if msg:
        sio.emit('chat-msg', {"msg": msg, "time_stamp": time.strftime('%b-%d %I:%M%p', time.localtime())}, to = session['room'])

@sio.on("join", namespace = "/game")
def join():
    room_row = db.session.query(Rooms).filter_by(room = session['room']).first()
    if not room_row:
        print(session['room'] + " is not a room")
        return
    join_room(session['room']) # which namespace joins the room?
    sio.emit('chat-msg', {"msg": session["username"] + " has joined room " + session["room"], "time_stamp": time.strftime('%b-%d %I:%M%p', time.localtime())}, to = session['room'], namespace = "/chat")
    connection_row = db.session.query(Connection).filter_by(room = session['room']).first()
    if connection_row:
        if session['username'] == room_row.user1:
            connection_row.user1_connect = True
        elif session['username'] == room_row.user2:
            connection_row.user2_connect = True
        if connection_row.live == "init" and (connection_row.user1_connect == True and connection_row.user2_connect == True):
            connection_row.live = "live"
            time_control = db.session.query(RoomInfo).filter_by(room = session['room']).first().time_control
            gameinfo = GameInfo(
                room = session['room'],
                fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                move_log = '',
                user1_last_move = None,
                user2_last_move = None,
                user1_time_left = timedelta(minutes = int(time_control)),
                user2_time_left = timedelta(minutes = int(time_control)),
                user1_score = 0,
                user2_score = 0
            )
            db.session.add(gameinfo)
            ### HERE IS WHERE START GAME EVENT TRIGGERED?
    elif session['username'] == room_row.user1:     
        connection = Connection(
            room = session['room'],
            user1_connect = True,
            user2_connect = False, 
            live = "init"
        )
        db.session.add(connection)
    db.session.commit()
    sio.emit('chess-update', to = session['room'])

# @sio.event
# def disconnect():
#     """
#     triggered when client disconnects to SocketIO
#     user is removed from their room, and the disconnect flag is set to True in case they come back within 20 seconds

#     :return: None
#     """
#     if session.get('room'):
#         time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
#         sio.emit('incoming-status-msg', {"msg": session["username"] + " has left room " + session["room"] , 'time_stamp': time_stamp}, to = session["room"])
#         leave_room(session["room"])
#         room_row = db.session.query(Room).filter_by(room = session['room']).first()
#         if not room_row:
#             sio.emit('route-index', to = request.sid)
#         elif session['username'] == room_row.user1:
#             room_row.user1_connect = False
#         elif session['username'] == room_row.user2:
#             room_row.user2_connect = False
#         db.session.commit()
#     else:
#         sio.emit('route-index', to = request.sid)
#     print(request.sid, ' disconnected')

# @sio.event
# def join(join_time):
#     """
#     connects a user to the desired room, and broadcasts that they connected to all users of the room
#     updates db and UI to account for join

#     :return: None
#     """
#     if session.get('room'):
#         room_row = db.session.query(Room).filter_by(room = session['room']).first()
#         if not room_row:
#             sio.emit('route-index', to = request.sid)
#         join_room(session['room'])
#         time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
#         sio.emit('incoming-status-msg', {"msg": session['username'] + " has joined room " + session['room'], 'time_stamp': time_stamp}, to = session['room'])
#         if session['username'] == room_row.user1:
#             room_row.user1_connect = True 
#         elif session['username'] == room_row.user2:
#             room_row.user2_connect = True
#         if room_row.live == False and (room_row.user1_connect == True and room_row.user2_connect == True): 
#             room_row.live = True
#             if room_row.user2_side == "black":
#                 room_row.user2_last_move = join_time 
#             else:
#                 room_row.user1_last_move = join_time
#             sio.emit('initialize-timers', to = session['room'])
#         db.session.commit()
#         sio.emit('update-ui', json.dumps({col.name: getattr(room_row, col.name) for col in room_row.__table__.columns}, default = str), to = session['room'])
# @sio.event
# def close_room():
#     """
#     closes the current room, deletes it from the db, and routes the user to index.

#     :return: None
#     """
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if room_row:
#         db.session.delete(room_row)
#         db.session.commit()
#     sio.emit('route-index', to = request.sid)

# @sio.event
# def check_connection(user):
#     """
#     checks that the opponent of user is still connected to the room, and sends result of check to receieve-ping event bucket

#     :param user: unique string for a user
#     :return: None
#     """
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         sio.emit('route-index', to = request.sid)
#         return
#     if user == session['username']:
#         if (session['username'] == room_row.user1 and not room_row.user2_connect) or (session['username'] == room_row.user2 and not room_row.user1_connect):
#             sio.emit('receive-ping', True, to = request.sid) 
#         else:
#             sio.emit('receive-ping', False, to = request.sid)


# @sio.event
# def new_game():
#     """
#     initializes a new game by switching sides and updating the UI + db

#     :return: None
#     """
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         sio.emit('route-index', to = request.sid)
#         return
#     room_row.user1_side = flip_side(room_row.user1_side)
#     room_row.user2_side = flip_side(room_row.user2_side)
#     room_row.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
#     room_row.move_log = ''
#     room_row.live = True
#     db.session.commit()
#     sio.emit('update-ui', {col.name: getattr(room_row, col.name) for col in room_row.__table__.columns}, to = session['room'])

# @sio.event
# def request_draw(user):
#     """
#     sends draw request to user, triggered by the other user

#     :param user: unique string for a user
#     :return: None
#     """
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         sio.emit('route-index', to = request.sid)
#         return
#     sio.emit('send-draw-request', user, to = session['room'])

# @sio.event
# def draw_result(draw):
#     """
#     sends draw result to both users in the room

#     :param draw: bool for whether or not the draw was accepted
#     :return: None
#     """
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         sio.emit('route-index', to = request.sid)
#         return
#     if draw:
#         room_row.live = False
#         # update score values in db here 
#         db.session.commit()
#     sio.emit('trigger-draw', draw, to = session['room'])

# @sio.event
# def resign_result(resign):
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         print("error")
#         flash("Lobby " + session['room'] + " doesn't exist!", 'error')
#     if resign:
#         room_row.live = False
#         db.session.commit()
#     sio.emit('trigger-resign', {"resign": resign, "user": session['username']}, to = session['room'])


# @sio.event
# def request_resign():
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         print("error")
#         flash("Lobby " + session['room'] + " doesn't exist!", 'error')
#     sio.emit('send-resign-request', to = request.sid)

# @sio.event
# def request_rematch(user):
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         print("error")
#         flash("Lobby " + session['room'] + " doesn't exist!", 'error')
#     if not room_row.live and room_row.user1_connect and room_row.user2_connect:
#         sio.emit('send-rematch-request', user, to = session['room'])
    
# @sio.event
# def rematch_result(rematch):
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     if not room_row:
#         print("error")
#         flash("Lobby " + session['room'] + " doesn't exist!", 'error')
    
#     sio.emit('trigger-rematch', rematch, to = session['room'])

# @sio.event
# def incoming_msg(data):
#     """
#     broadcasts message to all users in the desired room, with a timestamp of when they sent it

#     :param data: a dict in the form (username, room, message)
#     :return: None
#     """
#     username = data["username"]
#     room = data["room"]
#     msg = data["msg"]
#     time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
#     send({"username": username, "msg": msg, "time_stamp": time_stamp}, to = room)
    

# @sio.event
# def update(data):
#     room_row = db.session.query(Room).filter_by(room = session['room']).first()
#     room_row.fen = data['fen']
#     room_row.move_log += str(data['move'][0]) + '/' # separator
#     if data['user'] == room_row.user1: # user1 just made a move
#         room_row.user1_last_move = datetime.fromisoformat(data['timestamp'].replace('Z', ""))
#         room_row.user1_time_left -= (room_row.user2_last_move - room_row.user1_last_move) + timedelta(seconds = int(room_row.increment))
#     elif data['user'] == room_row.user2:
#         room_row.user2_last_move = datetime.fromisoformat(data['timestamp'].replace('Z', ""))
#         room_row.user2_time_left -= (room_row.user1_last_move - room_row.user2_last_move) + timedelta(seconds = int(room_row.increment))
#     db.session.commit()
#     sio.emit('update-db-values', {col.name: getattr(room_row, col.name) for col in room_row.__table__.columns}, to = session['room'])
#     sio.emit('update-board', data, to = session['room']) # should this only be sent to the user joining

# generates a unique 4-letter word from words.txt
def generate_key():
    lines = set()
    while True:
        line = random.randint(1, 500)
        if line not in lines:
            result = linecache.getline("words.txt", line)
            if not db.session.query(Rooms).filter_by(room = result).first():
                print(result.rstrip('\n'))
                return result.rstrip('\n')
            set.add(line)

# gets the opposite side for the given input side
def flip_side(side):
    if side == "white":
        return "black"
    elif side == "black":
        return "white"
    else:
        raise Exception("invalid side input")
