import random
import time
from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room
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
    if request.method == 'POST':
        if 'createSubmit' in request.form:

            # check if the room already exists in the database
            room_input = request.form.get("lobby")
            if db.session.query(Room).filter_by(room_name = room_input).first(): 
                return render_template("index.html")

            # create room from form fields
            # data:
            # room name
            # host username 
            # opp username None
            # side
            # time control
            # increment
            # current score
            
            username = request.form.get("username")
            side = request.form.get("btnradio")
            if side == "random":
                side = random.choice(["white", "black"])
            time_control = request.form.get("time-control")
            increment = request.form.get("increment")
            room = Room(
                room_name = room_input,
                host_username = username,
                opp_username = None
            )
            db.session.add(room)
            db.session.commit()

            session['username'] = username
            return redirect(url_for("create_lobby", lobby = room_input)) 
        elif 'joinSubmit' in request.form:
            room_input = request.form.get("lobby")
            username = request.form.get("username")
            session['username'] = username
            room_row = db.session.query(Room).filter_by(room_name = room_input).first()
            if not room_row or room_row.opp_username:
                return render_template("index.html")
            room_row.opp_username = username
            db.session.commit()
            return redirect(url_for("create_lobby", lobby = room_input))
    else:
        return render_template("index.html")

@app.route("/<lobby>", methods = ['GET', 'POST'])
def create_lobby(lobby):
    """
    creates a lobby and routes the user to that lobby.
    if a session for the user already exists, route them to the lobby 
    if user is a new opponent, retrieve the form data and add it to the db 

    :param lobby: unique string for a chess lobby
    :return: None
    """
    room_row = db.session.query(Room).filter_by(room_name = lobby).first()
    if not room_row:
        return render_template("index.html")
    
    data = {'username': None, 'lobby': lobby, 'modal': False}

    if request.method == 'POST':
        data['username'] = request.form.get('username')
        session['username'] = data['username']
        room_row.opp_username = data['username']
        db.session.commit()
        return render_template("room.html", data = data)
    if session.get("username"):
        data["username"] = session.get("username")
        if session.get("username") == room_row.host_username:
            return render_template("room.html", data = data)
        elif session.get("username") == room_row.opp_username:
            return render_template("room.html", data = data)
        elif not room_row.opp_username:
            room_row.opp_username = session.get("username")
            db.session.commit()
            return render_template("room.html", data = data)
        else:
            return render_template("index.html")
    else:
        data["modal"] = True
        return render_template("room.html", data = data)

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

    :param data: a dict in the form (username, room)
    :return: None
    """
    if data["username"] is not None:
        username = data["username"]
        room = data["room"]
        join_room(room)
        time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
        sio.emit('incoming-status-msg', {"msg": username + " has joined room " + room, 'time_stamp': time_stamp}, to = room)
    
@sio.event
def leave(data):
    """
    disconnects a user from the desired room, and broadcasts that they disconnected to all users of the room

    :param data: a dict in the form (username, room)
    :return: None
    """
    username = data["username"]
    room = data["room"]    
    time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    sio.emit('incoming-status-msg', {"msg": username + " has left room " + room, 'time_stamp': time_stamp}, to = room)
    leave_room(room)


@sio.event
def connect():
    print(request.sid, ' connected')
    ## EMIT HERE


@sio.event
def disconnect():
    print(request.sid, ' disconnected')





