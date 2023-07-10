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
                room_name = room_key,
                host_username = session['username'],
                opp_username = None,
                side = side,
                time_control = request.form.get("time_control"),
                increment = request.form.get("increment")
            )
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("create_room", room = session['room'])) 

        elif 'joinSubmit' in request.form:
            room_key = request.form.get("room")
            room_row = db.session.query(Room).filter_by(room_name = room_key).first()
            if not room_row:
                flash("Lobby " + room_key + " doesn't exist!", 'error')
                return render_template("index.html")
            if room_row.opp_username:
                flash("Lobby " + room_key + " is full!", 'error')
                return render_template("index.html")
            set_session_data(session, room_key, flip_side(room_row.side), request.form.get("username"), room_row.time_control, room_row.increment)
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
    room_row = db.session.query(Room).filter_by(room_name = room).first()
    if not room_row:
        flash("Lobby " + room + " doesn't exist!", 'error')
        return render_template("index.html")
    if request.method == 'POST':
        set_session_data(session, room, flip_side(room_row.side), request.form.get('username'), room_row.time_control, room_row.increment)
        room_row.opp_username = session['username']
        db.session.commit()
        return render_template("room.html", data = session, modal = False)
    if session.get("username"):
        if (session.get("username") == room_row.host_username and not room_row.opp_username) or session.get("username") == room_row.opp_username:
            return render_template("room.html", data = session, modal = False)
    else:
        if not room_row.opp_username:
            return render_template("room.html", data = session, modal = True)
    print("error creating a room")
    # should reroute to error route or something
    # flash("Lobby " + room + " is full!", 'error')
    # return render_template("index.html") 

app.route("/error", methods = ['GET', 'POST'])
def error():
    return render_template('error.html')

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
def join(data):
    """
    connects a user to the desired room, and broadcasts that they connected to all users of the room
    updates UI to account for join

    :param data: a dict in the form (username, room)
    :return: None
    """
    # JOINING WITH NO SESSION DATA
    join_room(session['room'])
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    sio.emit('incoming-status-msg', {"msg": session['username'] + " has joined room " + session['room'], 'time_stamp': time_stamp}, to = session['room'])

    # send enough info for both sides to completely fill out their names, and to flip the board accordingly
    room_row = db.session.query(Room).filter_by(room_name = session['room']).first()
    if session['username'] == room_row.host_username:
        opp_username = "Opponent" if not room_row.opp_username else room_row.opp_username
        sio.emit('update-ui', {"username": session['username'], "time_control": session['time_control'], "increment": session['increment'], "opp_username": opp_username, "side": session['side']}, to = session['room'])
    elif session['username'] == room_row.opp_username: 
        sio.emit('update-ui', {"username": session['username'], "time_control": session['time_control'], "increment": session['increment'], "opp_username": room_row.host_username, "side": session['side']}, to = session['room'])
    else:
        raise Exception("Joining room illegally")

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
    session.clear()

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
        room_row = db.session.query(Room).filter_by(room_name = session['room']).first()
        if room_row.host_username == session['username']:
            room_row.host_username == None
        elif room_row.opp_username == session['username']:
            room_row.opp_username == None 
    print(request.sid, ' disconnected')
    #upon disconnect, room should shut down and database row should be deleted (for now)

# generates a unique key of length n 
def generate_key(n):
    while True:
        result = ""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        for i in range(n):
            result += random.choice(chars)
        if not db.session.query(Room).filter_by(room_name = result).first(): 
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




