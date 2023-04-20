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
    # if request.method != 'POST':
    #     return render_template('index.html')
    # else:
    #     if 'createSubmit' in request.form:
    #         room_name = 

@sio.event
def connect():
    print(request.sid, ' connected')
    room = Room(
        room_name = "test room",
        host_username = "test username",
        opp_username = None
    )
    db.session.add(room)
    db.session.commit()

@sio.event
def disconnect():
    print(request.sid, ' disconnected')





