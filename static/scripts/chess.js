import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

const socket = io("/game");

// HTML-READ VALUES
let room = document.getElementById("room-data").getAttribute("data-value");
let username = document.getElementById("username-data").getAttribute("data-value");

// ROOM-INFO VALUES
let opp_username;
let side;
let opp_side;
let time_control;
let increment;

// CONNECTION VALUES
let live;

// GAME-INFO VALUES
let fen;
let move_log;
let time_left;
let opp_time_left;
let score;
let opp_score;

// CHESS VALUES
const config = {
    draggable: true,
    position: 'start',
    showErrors: 'console',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    dropOffBoard: 'snapback'
};
let board = Chessboard('board1', config);
let game = new Chess();

// ###################
// # SOCKETIO EVENTS #
// ###################

socket.on('connect', () => {
    console.log("connected to chess game");
    document.getElementById("link").innerHTML = "thechesskey.com/" + room;
    document.getElementById("username").innerHTML = username;
    socket.emit('join'); 
});

// add roomname innerhtml update
socket.on('game-roominfo', data => {
    time_control = data['time_control'];
    increment = data['increment'];
    if (username == data['user1']) {
        if (data['user2'] != null) {
            opp_username = data['user2'];
        } else {
            opp_username = "Opponent";
        }
        side = data['user1_side'];
        opp_side = data['user2_side']
        
    } else {
        opp_username = data['user1'];
        side = data['user2_side'];
        opp_side = data['user1_side'];
    } 
    document.getElementById("opp_username").innerHTML = opp_username;
    document.getElementById("scoreboard").innerHTML = username;
    document.getElementById("opp_scoreboard").innerHTML = opp_username;
    document.getElementById("time_left").innerHTML = time_control;
    document.getElementById("opp_time_left").innerHTML = time_control;
    board.orientation(side); 
});

socket.on('game-connection', live_value => {
    console.log("Live: " + live_value);
    live = live_value;
});

socket.on('game-gameinfo', data => {
    data = JSON.parse(data);
    console.log(data);
    fen = data['fen'];
    move_log = data['move_log'];
    if (username == data['user1']) {
        time_left = data['user1_time_left'];
        score = data['user1_score'];
        opp_time_left = data['user2_time_left'];
        opp_score = data['user2_score'];
    } else {
        time_left = data['user2_time_left'];
        score = data['user2_score'];
        opp_time_left = data['user1_time_left'];
        opp_score = data['user1_score'];
    }
    document.getElementById("score").innerHTML = score;
    document.getElementById("opp_score").innerHTML = opp_score;
    document.getElementById("time_left").innerHTML = time_left
    document.getElementById("opp_time_left").innerHTML = opp_time_left;

    console.log(fen);
    console.log(move_log);
    console.log(time_left);
    console.log(opp_time_left);
    console.log(score);
    console.log(opp_score);

    game.load(data['fen']);
    board.position(game.fen());
    updateGameLog();
});


function updateGameLog() {
    let moveArray = move_log.split("/");
    moveArray.pop();
    console.log(moveArray);
    let gameLog = document.getElementById("game-log");
    let gameLogLength = gameLog.children.length;

    if (moveArray.length == gameLogLength){
        console.log("got here");
        return;
    } else if (moveArray.length == 0){
        gameLog.innerHTML = '';
    } else {
        for (let i = gameLogLength; i < moveArray.length; i++) {
            console.log(moveArray[i]);
            let p = document.createElement('p');
            p.classList.add('odd:text-black', 'flex-[50%]', 'pl-2');
            if (i % 2 == 0) {
                p.innerHTML = (Math.floor(i / 2) + 1).toString() + ". ";
            }
            p.innerHTML += moveArray[i];
            gameLog.append(p);
        }
    }
    gameLog.scrollTop = gameLog.scrollHeight;
}

function onDragStart (source, piece, position, orientation) {
    if (live != "live" 
        || !isTurn()
        || game.isGameOver()
        || (game.turn() === 'w' && piece.search(/^b/) !== -1)
        || (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
            return false;
        }
        console.log("valid move");
  }

  function onDrop (source, target) {
    try {
      game.move({
        from: source,
        to: target,
        promotion: 'q' 
      });
    }
    catch (err) {
        console.log("error making move");
        return 'snapback';
    }
    console.log("making move");
    socket.emit('make_move', {"move": game.history().slice(-1), "fen": game.fen(), "user": username, "increment": increment});
  }

  function onSnapEnd() {
    board.position(game.fen());
  }

  function isTurn() {
    if ((game.turn() == "w" && side == "white") || (game.turn() == "b" && side == "black")) return true
    return false;
  }

$(window).resize(board.resize);

});