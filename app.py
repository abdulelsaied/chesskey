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
            session.clear()
            room_input = request.form.get("lobby")
            if db.session.query(Room).filter_by(room_name = room_input).first(): 
                print("room already exists - cant create")
                return render_template("index.html")

            side = request.form.get("btnradio")
            if side == "random":
                side = random.choice(["white", "black"])
            
            session['username'] = request.form.get("username")
            session['side'] = side
            session['time_control'] = request.form.get("time-control")
            session['increment'] = request.form.get("increment")
            session['room'] = room_input
            room = Room(
                room_name = room_input,
                host_username = session['username'],
                opp_username = None,
                side = side,
                time_control = request.form.get("time-control"),
                increment = request.form.get("increment")
            )
            db.session.add(room)
            db.session.commit()

            print("creating room", room_input, "host username", session['username'], "opp username", None)
            return redirect(url_for("create_lobby", lobby = session['room'])) 

        elif 'joinSubmit' in request.form:
            session.clear()
            room_input = request.form.get("lobby")
            room_row = db.session.query(Room).filter_by(room_name = room_input).first()
            if not room_row:
                print("room doesn't exist")
                return render_template("index.html")
            if room_row.opp_username:
                print("room is already full")
                return render_template("index.html")
            session['username'] = request.form.get("username")
            session['room'] = room_input
            room_row.opp_username = session['username']
            db.session.commit()
            print("joining room", session['room'], "host username", room_row.host_username, "opp username", session['username'])
            # data = {'lobby': room_input, 'side': None, 'time_control': None, 'increment': None}
            return redirect(url_for("create_lobby", lobby = session['room']))
    else:
        print("get request in /")
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
        print("room doesn't exist")
        return render_template("index.html")
    
    data = {}
    data['username'] = None
    data['lobby'] = lobby
    data['modal'] = False
    data['side'] = None

    if request.method == 'POST':
        data['username'] = request.form.get('username')
        session['username'] = data['username']
        room_row.opp_username = data['username']
        data['side'] = "white" if room_row.side == "black" else "black" 
        db.session.commit()
        print("received modal data for opp")
        return render_template("room.html", data = data)
    if session.get("username"):
        data["username"] = session.get("username")
        if session.get("username") == room_row.host_username:
            print("session for host already existed")
            data['side'] = room_row.side
            return render_template("room.html", data = data)
        elif session.get("username") == room_row.opp_username:
            print("session for opp already existed")
            data['side'] = "white" if room_row.side == "black" else "black" 
            return render_template("room.html", data = data)
        elif not room_row.opp_username:
            room_row.opp_username = session.get("username")
            db.session.commit()
            data['side'] = "white" if room_row.side == "black" else "black"
            return render_template("room.html", data = data)
        else:
            print("wasnt a session user or routed from index")
            return render_template("index.html")
    else:
        data["modal"] = True
        print("new user, prompt modal ")
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
    updates UI to account for join

    :param data: a dict in the form (username, room)
    :return: None
    """
    if data["username"] is not None:
        username = data["username"]
        room = data["room"]
        session['room'] = room
        join_room(room)
        time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
        sio.emit('incoming-status-msg', {"msg": username + " has joined room " + room, 'time_stamp': time_stamp}, to = room)

        # send enough info for both sides to completely fill out their names, and to flip the board accordingly
        room_row = db.session.query(Room).filter_by(room_name = room).first()
        if username == room_row.host_username:
            opp_username = "Opponent" if not room_row.opp_username else room_row.opp_username
            sio.emit('update-ui', {"username": username, "time_control": room_row.time_control, "increment": room_row.increment, "opp_username": opp_username, "side": room_row.side}, to = room)
        elif username == room_row.opp_username:
            side = "white" if room_row.side == "black" else "black" 
            sio.emit('update-ui', {"username": username, "time_control": room_row.time_control, "increment": room_row.increment, "opp_username": room_row.host_username, "side": side}, to = room)
        else:
            print("error")

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
    session.pop('room')

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





