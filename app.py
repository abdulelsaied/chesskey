import random
import time
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_socketio import SocketIO, send, join_room, leave_room
from db import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = '0351638baf53bbdac142a7e49d898cf490d2c870f2a275769e9fdbef6e646476'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://chesskey_user:xpBr1LvqQh8M5d7BfLeLZhUloHkmGWgn@dpg-ch0pv96si8uipc8h8a9g-a.oregon-postgres.render.com/chesskey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

sio = SocketIO(app)

@app.route("/", methods = ['GET', 'POST'])
def index():
    """
    routes the user to the landing page.
    POST data can be from the create form or the post form, and the db fields are filled accordingly

    :return: None
    """
    session.clear()
    if request.method == 'POST':
        if 'createSubmit' in request.form:
            room_key = generate_key(3)
            side = request.form.get("btnradio")
            if side == "random":
                side = random.choice(["white", "black"])
            set_session_data(session, room_key, side, request.form.get("username"), request.form.get("time_control"), request.form.get("increment"))
            room = Room(
                room = room_key,
                user1 = session['username'],
                user2 = None,
                user1_side = side,
                time_control = request.form.get("time_control"),
                increment = request.form.get("increment"),
                user1_disconnect = False,
                user2_disconnect = False
            )
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("create_room", room = session['room'])) 

        elif 'joinSubmit' in request.form:
            room_key = request.form.get("room")
            room_row = db.session.query(Room).filter_by(room = room_key).first()
            if not room_row:
                flash("Lobby " + room_key + " doesn't exist!", 'error')
                return render_template("index.html")
            if room_row.user2 and room_row.user1:
                flash("Lobby " + room_key + " is full!", 'error')
                return render_template("index.html")
            set_session_data(session, room_key, flip_side(room_row.user1_side), request.form.get("username"), room_row.time_control, room_row.increment)
            room_row.opp_username = session['username']
            db.session.commit()
            return redirect(url_for("create_room", room = session['room']))
    else:
        return render_template("index.html")

@app.route("/<room>", methods = ['GET', 'POST'])
def create_room(room):
    """
    creates a room and routes the user to that lobby.
    if a session for the user already exists, route them to the lobby 
    if user is a new opponent, retrieve the form data and add it to the db 

    :param lobby: unique string for a chess lobby
    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = room).first()
    if not room_row:
        flash("Lobby " + room + " doesn't exist!", 'error')
        return render_template("index.html")
    if request.method == 'POST':
        set_session_data(session, room, flip_side(room_row.user1_side), request.form.get('username'), room_row.time_control, room_row.increment)
        room_row.user2 = session['username']
        db.session.commit()
        return render_template("room.html", data = session, modal = False) # render a different template 
    if session.get("username"):
        if session.get("username") == room_row.user1 or session.get("username") == room_row.user2: 
            session['room'] = room_row.room
            return render_template("room.html", data = session, modal = False)
    else:
        if not room_row.user2:
            return render_template("room.html", data = session, modal = True)
    flash("Lobby " + room + " is full!", 'error')
    session.clear()
    return redirect(url_for("index")) 

@sio.event
def check_connection():
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        flash("Lobby " + session['room'] + " doesn't exist!", 'error')
        return render_template("index.html")
    if (session['username'] == room_row.user1 and room_row.user2_disconnect) or (session['username'] == room_row.user2 and room_row.user1_disconnect):
        sio.emit('receive-ping', True, to = request.sid) 
    else:
        sio.emit('receive-ping', False, to = request.sid)

@sio.event
def close_room():
    print("closing room " + session['room'])
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    db.session.delete(room_row)
    db.session.commit()
    session.clear()
    flash("Opponent left the room")
    return redirect(url_for("index")) 
    

@sio.event
def incoming_msg(data):
    """
    broadcasts message to all users in the desired room, with a timestamp of when they sent it

    :param data: a dict in the form (username, room, message)
    :return: None
    """
    username = data["username"]
    room = data["room"]
    msg = data["msg"]
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    send({"username": username, "msg": msg, "time_stamp": time_stamp}, to = room)


@sio.event
def join():
    """
    connects a user to the desired room, and broadcasts that they connected to all users of the room
    updates UI to account for join

    :param data: a dict in the form (username, room)
    :return: None
    """
    if session.get('room'):
        join_room(session['room'])
        time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
        sio.emit('incoming-status-msg', {"msg": session['username'] + " has joined room " + session['room'], 'time_stamp': time_stamp}, to = session['room'])

        # send enough info for both sides to completely fill out their names, and to flip the board accordingly
        room_row = db.session.query(Room).filter_by(room = session['room']).first()
        if not room_row:
            flash("Room doesn't exist anymore")
            return redirect(url_for("index"))
        if session['username'] == room_row.user1:
            room_row.user1_disconnect = False 
            user2 = "Opponent" if not room_row.user2 else room_row.user2
            sio.emit('update-ui', {"username": session['username'], "time_control": session['time_control'], "increment": session['increment'], "opp_username": user2, "side": session['side']}, to = session['room'])
        elif session['username'] == room_row.user2: # and its the first time connecting?
            room_row.user2_disconnect = False
            sio.emit('update-ui', {"username": session['username'], "time_control": session['time_control'], "increment": session['increment'], "opp_username": room_row.user1, "side": session['side']}, to = session['room'])
            sio.emit('initialize-game', to = session['room'])
        else:
            raise Exception("Joining room illegally")
    else:
        raise Exception("Session doesn't exist")
    db.session.commit()

@sio.event
def leave(data):
    """
    disconnects a user from the desired room, and broadcasts that they disconnected to all users of the room

    :param data: a dict in the form (username, room)
    :return: None
    """  
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    sio.emit('incoming-status-msg', {"msg": data["username"] + " has left room " + data["room"] , 'time_stamp': time_stamp}, to = data["room"])
    leave_room(data["room"])

@sio.event
def update(data):
    sio.emit('update-board', data, to = data['room'])

@sio.event
def connect():
    print(request.sid, ' connected')

@sio.event
def disconnect():
    if session.get('room'):
        sio.emit('incoming-status-msg', {"msg": session['username'] + " has left room " + session['room'], 'time_stamp': time.strftime('%b-%d %I:%M%p', time.localtime())}, to = session['room'])
        room_row = db.session.query(Room).filter_by(room = session['room']).first()
        if session['username'] == room_row.user1:
            room_row.user1_disconnect = True
        elif session['username'] == room_row.user2:
            room_row.user2_disconnect = True 
        db.session.commit()
    print(request.sid, ' disconnected')



# generates a unique key of length n 
def generate_key(n):
    while True:
        result = ""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        for i in range(n):
            result += random.choice(chars)
        if not db.session.query(Room).filter_by(room = result).first(): 
            return result

def flip_side(side):
    if side == "white":
        return "black"
    elif side == "black":
        return "white"
    else:
        raise Exception("Invalid side value")

def set_session_data(session, room, side, username, time_control, increment):
    session['room'] = room
    session['side'] = side
    session['username'] = username
    session['time_control'] = time_control
    session['increment'] = increment




