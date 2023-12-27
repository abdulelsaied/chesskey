import os
import random
import time
import json
import linecache
import datetime
from datetime import timedelta, timezone
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
                return render_template("landing.html")
            session['room'] = room_key
            session['username'] = request.form.get("username") 
            if session['username'] == room_row.user1:
                print("same username as user1 inputted")
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
    if room == "favicon.ico" or (request.method == 'POST' and request.form.get('msg') == 'index'):
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

###################
# GAME EVENTS #
###################

@sio.on("connect", namespace = '/game')
def connect():
    """
    triggered when client connects to game socket

    :return: None
    """
    print(request.sid, ' connected to game')

# @sio.on("disconnect", namespace = "/game")
# def disconnect():
#     """
#     triggered when client disconnects to SocketIO
#     user is removed from their room, and the disconnect flag is set to True in case they come back within 20 seconds

#     :return: None
#     """
#     if session.get('room'):
#         sio.emit('chat-msg', {"msg": session["username"] + " has left room " + session["room"]}, to = session["room"])
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

@sio.on("join", namespace = '/game')
def join():
    room_row = db.session.query(Rooms).filter_by(room = session['room']).first()
    if not room_row:
        print(session['room'] + " is not a room")
        return
    join_room(session['room'])
    sio.emit('chat-msg', session["username"] + " has joined room " + session["room"], to = session['room'], namespace = "/chat")
    connection_row = db.session.query(Connection).filter_by(room = session['room']).first()
    roominfo_row = db.session.query(RoomInfo).filter_by(room = session['room']).first()
    if connection_row:
        if session['username'] == room_row.user1:
            connection_row.user1_connect = True
        elif session['username'] == room_row.user2:
            connection_row.user2_connect = True
        if connection_row.live == "init" and (connection_row.user1_connect == True and connection_row.user2_connect == True):
            sio.emit('chat-msg', "Game has begun!", to = session['room'], namespace = "/chat")
            sio.emit('play-sound', "start", to = session['room'], namespace = "/game")
            connection_row.live = "live"
            time_control = roominfo_row.time_control
            # upon creation of gameinfo, set the timer of the black player to be the current UTC timestamp 
            gameinfo = GameInfo(
                room = session['room'],
                fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                move_log = '',
                user1_last_move = datetime.datetime.now(timezone.utc) if roominfo_row.user1_side == "black" else None,
                user2_last_move = datetime.datetime.now(timezone.utc) if roominfo_row.user2_side == "black" else None,
                user1_time_left = timedelta(minutes = int(time_control)),
                user2_time_left = timedelta(minutes = int(time_control)),
                user1_score = 0,
                user2_score = 0
            )
            db.session.add(gameinfo)   
    elif session['username'] == room_row.user1:     
        connection = Connection(
            room = session['room'],
            user1_connect = True,
            user2_connect = False, 
            live = "init"
        )
        db.session.add(connection)

    db.session.commit()

    ### which one of these should be ONLY to request.sid (do both users need this information wwhen the other joins)
    connection_row = db.session.query(Connection).filter_by(room = session['room']).first()
    sio.emit('game-roominfo', {"user1": room_row.user1, "user2": room_row.user2, "user1_side": roominfo_row.user1_side, "user2_side": roominfo_row.user2_side, "time_control": str(timedelta(minutes = int(roominfo_row.time_control))), "increment": roominfo_row.increment}, to = session['room'], namespace = "/game")
    sio.emit('game-connection', {"live": connection_row.live}, to = session['room'], namespace = "/game") 
    game_row = db.session.query(GameInfo).filter_by(room = session['room']).first() 
    if game_row:
        game_dict = {col.name: getattr(game_row, col.name) for col in game_row.__table__.columns}
        game_dict.update({"user1": room_row.user1})
        print(json.dumps(game_dict, default = str))
        sio.emit('game-gameinfo', json.dumps(game_dict, default = str), to = session['room'], namespace = "/game")

@sio.on("make_move", namespace = '/game')
def make_move(data):
    room_row = db.session.query(Rooms).filter_by(room = session['room']).first()
    roominfo_row = db.session.query(RoomInfo).filter_by(room = session['room']).first()
    game_row = db.session.query(GameInfo).filter_by(room = session['room']).first()
    game_row.fen = data['fen']
    game_row.move_log += str(data['move'][0]) + '/' 
    if data['user'] == room_row.user1:
        game_row.user1_last_move = datetime.datetime.now(timezone.utc)
        game_row.user1_time_left = game_row.user1_time_left - (datetime.datetime.now(timezone.utc) - game_row.user2_last_move.replace(tzinfo = timezone.utc)) + timedelta(seconds = int(data['increment']))
        if game_row.user1_time_left < timedelta(0):
            game_over({"flag": 1, "side": roominfo_row.user2_side, "reason": "by timeout"})
    elif data['user'] == room_row.user2:
        game_row.user2_last_move = datetime.datetime.now(timezone.utc)
        game_row.user2_time_left = game_row.user2_time_left - (datetime.datetime.now(timezone.utc) - game_row.user1_last_move.replace(tzinfo = timezone.utc)) + timedelta(seconds = int(data['increment']))
        if game_row.user2_time_left < timedelta(0):
            game_over({"flag": 1, "side": roominfo_row.user1_side, "reason": "by timeout"})
    db.session.commit()

    game_dict = {col.name: getattr(game_row, col.name) for col in game_row.__table__.columns}
    game_dict.update({"user1": room_row.user1})
    print(json.dumps(game_dict, default = str))
    sio.emit('game-gameinfo', json.dumps(game_dict, default = str), to = session['room'], namespace = "/game")

@sio.on("game_over", namespace = "/game")
def game_over(data):
    connection_row = db.session.query(Connection).filter_by(room = session['room']).first()
    connection_row.live = "over"

    room_row = db.session.query(Rooms).filter_by(room = session['room']).first()
    roominfo_row = db.session.query(RoomInfo).filter_by(room = session['room']).first()
    game_row = db.session.query(GameInfo).filter_by(room = session['room']).first()
    if data['flag'] == 0:
        game_row.user1_score += 0.5
        game_row.user2_score += 0.5
    elif data['flag'] == 1:
        if roominfo_row.user1_side == data['side']:
            game_row.user1_score += 1
        else: 
            game_row.user2_score += 1 

    db.session.commit() 
    game_dict = {col.name: getattr(game_row, col.name) for col in game_row.__table__.columns}
    game_dict.update({"user1": room_row.user1})

    sio.emit('game-gameinfo', json.dumps(game_dict, default = str), to = session['room'], namespace = "/game")
    sio.emit('game-connection', {"live": connection_row.live, "side": data['side'], "reason": data['reason'], "flag": data['flag']}, to = session['room'], namespace = "/game") 

@sio.on("new_game", namespace = "/game")
def new_game():

    room_row = db.session.query(Rooms).filter_by(room = session['room']).first()

    roominfo_row = db.session.query(RoomInfo).filter_by(room = session['room']).first()
    roominfo_row.user1_side = flip_side(roominfo_row.user1_side)
    roominfo_row.user2_side = flip_side(roominfo_row.user2_side)
    db.session.commit()

    connection_row = db.session.query(Connection).filter_by(room = session['room']).first()
    connection_row.live = "live"

    game_row = db.session.query(GameInfo).filter_by(room = session['room']).first()
    game_row.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    game_row.move_log = ''
    game_row.user1_last_move = datetime.datetime.now(timezone.utc) if roominfo_row.user1_side == "black" else None
    game_row.user2_last_move = datetime.datetime.now(timezone.utc) if roominfo_row.user2_side == "black" else None
    game_row.user1_time_left = timedelta(minutes = int(roominfo_row.time_control))
    game_row.user2_time_left = timedelta(minutes = int(roominfo_row.time_control))

    db.session.commit()

    game_dict = {col.name: getattr(game_row, col.name) for col in game_row.__table__.columns}
    game_dict.update({"user1": room_row.user1})
    print("new game dict ")
    print("-----")
    print(game_dict)

    sio.emit('game-roominfo', {"user1": room_row.user1, "user2": room_row.user2, "user1_side": roominfo_row.user1_side, "user2_side": roominfo_row.user2_side, "time_control": str(timedelta(minutes = int(roominfo_row.time_control))), "increment": roominfo_row.increment}, to = session['room'], namespace = "/game")
    sio.emit('game-gameinfo', json.dumps(game_dict, default = str), to = session['room'], namespace = "/game")
    sio.emit('game-connection', {"live": connection_row.live}, to = session['room'], namespace = "/game") 

    sio.emit('play-sound', "start", to = session['room'], namespace = "/game")

@sio.on("draw_request", namespace = "/game")
def draw_request(data):
    sio.emit('display-draw-request', data, to = session['room'], namespace = "/game")

@sio.on("rematch_request", namespace = "/game")
def rematch_request(data):
    sio.emit('display-rematch-request', data, to = session['room'], namespace = "/game")

@sio.on("play_move_sound", namespace = "/game")
def play_move_sound(move_string):
    print(move_string)
    if "#" in move_string:
        sio.emit('play-sound', "over", to = session['room'], namespace = "/game")
    elif "+" in move_string:
        sio.emit('play-sound', "check", to = session['room'], namespace = "/game")
    elif "-" in move_string:
        sio.emit('play-sound', "castle", to = session['room'], namespace = "/game")
    elif "x" in move_string:
        sio.emit('play-sound', "capture", to = session['room'], namespace = "/game")
    else:
        sio.emit('play-sound', "move", to = session['room'], namespace = "/game")

###################
# CHAT EVENTS #
###################

@sio.on("connect", namespace = '/chat')
def connect():
    """
    triggered when client connects to chat socket

    :return: None
    """
    print(request.sid, ' connected to chat')

@sio.on("join", namespace = '/chat')
def join():
    join_room(session['room'])

@sio.on("chat_msg", namespace = '/chat')
def chat_msg(msg):
    if msg:
        sio.emit('chat-msg', msg, to = session['room'], namespace = "/chat")


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

def generate_key():
    lines = set()
    while True:
        line = random.randint(1, 500)
        if line not in lines:
            result = linecache.getline("words.txt", line).rstrip('\n')
            if not db.session.query(Rooms).filter_by(room = result).first():
                print(result)
                return result
            lines.add(line)

# gets the opposite side for the given input side
def flip_side(side):
    if side == "white":
        return "black"
    else:
        return "white"
