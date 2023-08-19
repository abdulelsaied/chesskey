import random
import time
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_socketio import SocketIO, send, join_room, leave_room
from db import *
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = '0351638baf53bbdac142a7e49d898cf490d2c870f2a275769e9fdbef6e646476'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://chesskey2_0_user:iL6o4g32rc6IXiDLN1F5vsd9rTr2nrIY@dpg-cis7u7p8g3n42olp6mqg-a.oregon-postgres.render.com/chesskey2_0'
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
            room_key = generate_key(3)
            side = random.choice(["white", "black"]) if request.form.get("btnradio") == "random" else request.form.get("btnradio")
            session['room'] = room_key
            session['username'] = request.form.get("username")
            room = Room(
                room = room_key,
                user1 = request.form.get("username"),
                user2 = None,
                user1_side = side,
                user2_side = flip_side(side),
                time_control = request.form.get("time_control"),
                increment = request.form.get("increment"),
                user1_connect = False,
                user2_connect = False, 
                live = False,
                fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                move_log = '', 
                user1_last_move = None,
                user2_last_move = None
            )
            db.session.add(room)
            db.session.commit()
            return redirect(url_for("create_room", room = session['room'])) 
        elif 'joinSubmit' in request.form:
            room_key = request.form.get("room")
            room_row = db.session.query(Room).filter_by(room = room_key).first()
            if not room_row:
                return render_template("index.html", alert = {"msg": "Lobby " + room_key + " doesn't exist!", "type": "danger"})
            if room_row.user2 and room_row.user1:
                return render_template("index.html", alert = {"msg": "Lobby " + room_key + " is full!", "type": "danger"})
            session['room'] = room_key
            session['username'] = request.form.get("username") 
            room_row.user2 = session['username']
            db.session.commit()
            return redirect(url_for("create_room", room = session['room']))
    else:
        msg = session.get('message', "")
        type = session.get('type', "")
        session.clear()
        return render_template("index.html", alert = {"msg": msg, "type": type})

@app.route("/<room>", methods = ['GET', 'POST'])
def create_room(room):
    """
    creates a room and routes the user to that lobby.

    :param lobby: unique string for a chess lobby
    :return: None
    """
    if request.method == 'POST' and request.form.get('msg') == 'index':
        session['message'] = "Lobby " + room + " has been closed!"
        session['type'] = "danger"
        return redirect(url_for("index")) 
    room_row = db.session.query(Room).filter_by(room = room).first()
    if not room_row:
        session['message'] = "Lobby " + room + " doesn't exist!"
        session['type'] = 'danger'
        return redirect(url_for("index")) 
    if request.method == 'POST':
        session['room'] = room
        session['username'] = request.form.get('username')
        room_row.user2 = session['username']
        db.session.commit()
        return render_template("room.html", data = session, modal = False) # render a different template 
    if session.get("username"):
        if session.get("username") == room_row.user1 or session.get("username") == room_row.user2: 
            session['room'] = room_row.room
            return render_template("room.html", data = session, modal = False)
    else:
        if not room_row.user2:
            return render_template("room.html", data = session, modal = True) # render a different template
    session['message'] = "Lobby " + room + " is full!"
    session['type'] = "danger"
    return redirect(url_for("index")) 

###################
# SOCKETIO EVENTS #
###################

@sio.event
def connect():
    """
    triggered when client connects to SocketIO

    :return: None
    """
    print(request.sid, ' connected')

@sio.event
def disconnect():
    """
    triggered when client disconnects to SocketIO
    user is removed from their room, and the disconnect flag is set to True in case they come back within 20 seconds

    :return: None
    """
    if session.get('room'):
        time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
        sio.emit('incoming-status-msg', {"msg": session["username"] + " has left room " + session["room"] , 'time_stamp': time_stamp}, to = session["room"])
        leave_room(session["room"])
        room_row = db.session.query(Room).filter_by(room = session['room']).first()
        if not room_row:
            sio.emit('route-index', to = request.sid)
        elif session['username'] == room_row.user1:
            room_row.user1_connect = False
        elif session['username'] == room_row.user2:
            room_row.user2_connect = False
        db.session.commit()
    else:
        sio.emit('route-index', to = request.sid)
    print(request.sid, ' disconnected')

@sio.event
def join():
    """
    connects a user to the desired room, and broadcasts that they connected to all users of the room
    updates db and UI to account for join

    :return: None
    """
    if session.get('room'):
        room_row = db.session.query(Room).filter_by(room = session['room']).first()
        if not room_row:
            flash("Room doesn't exist anymore")
            sio.emit('route-index', to = request.sid)
            print("got here")
        join_room(session['room'])
        time_stamp = time.strftime('%b-%d %I:%M%p', time.localtime())
        sio.emit('incoming-status-msg', {"msg": session['username'] + " has joined room " + session['room'], 'time_stamp': time_stamp}, to = session['room'])
        if session['username'] == room_row.user1:
            room_row.user1_connect = True 
        elif session['username'] == room_row.user2:
            room_row.user2_connect = True
        if room_row.live == False and (room_row.user1_connect == True and room_row.user2_connect == True): 
            room_row.live = True
        db.session.commit()
        print({col.name: getattr(room_row, col.name) for col in room_row.__table__.columns})
        sio.emit('update-ui', {col.name: getattr(room_row, col.name) for col in room_row.__table__.columns}, to = session['room'])

@sio.event
def close_room():
    """
    closes the current room, deletes it from the db, and routes the user to index.

    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if room_row:
        db.session.delete(room_row)
        db.session.commit()
    sio.emit('route-index', to = request.sid)

@sio.event
def check_connection(user):
    """
    checks that the opponent of user is still connected to the room, and sends result of check to receieve-ping event bucket

    :param user: unique string for a user
    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        sio.emit('route-index', to = request.sid)
        return
    if user == session['username']:
        if (session['username'] == room_row.user1 and not room_row.user2_connect) or (session['username'] == room_row.user2 and not room_row.user1_connect):
            sio.emit('receive-ping', True, to = request.sid) 
        else:
            sio.emit('receive-ping', False, to = request.sid)


@sio.event
def new_game():
    """
    initializes a new game by switching sides and updating the UI + db

    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        sio.emit('route-index', to = request.sid)
        return
    room_row.user1_side = flip_side(room_row.user1_side)
    room_row.user2_side = flip_side(room_row.user2_side)
    room_row.fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    room_row.move_log = ''
    room_row.live = True
    db.session.commit()
    sio.emit('update-ui', {col.name: getattr(room_row, col.name) for col in room_row.__table__.columns}, to = session['room'])

@sio.event
def request_draw(user):
    """
    sends draw request to user, triggered by the other user

    :param user: unique string for a user
    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        sio.emit('route-index', to = request.sid)
        return
    sio.emit('send-draw-request', user, to = session['room'])

@sio.event
def draw_result(draw):
    """
    sends draw result to both users in the room

    :param draw: bool for whether or not the draw was accepted
    :return: None
    """
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        sio.emit('route-index', to = request.sid)
        return
    if draw:
        room_row.live = False
        # update score values in db here 
        db.session.commit()
    sio.emit('trigger-draw', draw, to = session['room'])

@sio.event
def resign_result(resign):
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        print("error")
        flash("Lobby " + session['room'] + " doesn't exist!", 'error')
    if resign:
        room_row.live = False
        db.session.commit()
    sio.emit('trigger-resign', {"resign": resign, "user": session['username']}, to = session['room'])


@sio.event
def request_resign():
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        print("error")
        flash("Lobby " + session['room'] + " doesn't exist!", 'error')
    sio.emit('send-resign-request', to = request.sid)

@sio.event
def request_rematch(user):
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        print("error")
        flash("Lobby " + session['room'] + " doesn't exist!", 'error')
    if not room_row.live and room_row.user1_connect and room_row.user2_connect:
        sio.emit('send-rematch-request', user, to = session['room'])
    
@sio.event
def rematch_result(rematch):
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    if not room_row:
        print("error")
        flash("Lobby " + session['room'] + " doesn't exist!", 'error')
    
    sio.emit('trigger-rematch', rematch, to = session['room'])

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
def update(data):
    # here is where the db values should be updated, then sent to the update-board bucket
    room_row = db.session.query(Room).filter_by(room = session['room']).first()
    room_row.fen = data['fen']
    room_row.move_log += str(data['move'][0]) + '/' # separator
    if data['user'] == room_row.user1:
        room_row.user1_last_move = data['timestamp']
    elif data['user'] == room_row.user2:
        room_row.user2_last_move = data['timestamp']
    db.session.commit()
    sio.emit('update-board', data, to = session['room']) # should this only be sent to the user joining

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
        raise Exception("invalid side input")
