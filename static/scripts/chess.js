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
let last_move;
let opp_last_move;
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
    board.orientation(side); 
});

socket.on('game-connection', live_value => {
    console.log("Live: " + live_value);
    live = live;
});

socket.on('game-gameinfo', data => {
    fen = data['fen'];
    move_log = data['move_log'];
    if (username == data['user1']) {
        last_move = data['user1_last_move'];
        time_left = data['user1_time_left'];
        score = data['user1_score'];
        opp_last_move = data['user2_last_move'];
        opp_time_left = data['user2_time_left'];
        opp_score = data['user2_score'];
    } else {
        last_move = data['user2_last_move'];
        time_left = data['user2_time_left'];
        score = data['user2_score'];
        opp_last_move = data['user1_last_move'];
        opp_time_left = data['user1_time_left'];
        opp_score = data['user1_score'];
    }
    document.getElementById("score").innerHTML = score;
    document.getElementById("opp_score").innerHTML = opp_score;
    document.getElementById("time_left").innerHTML = time_left
    document.getElementById("opp_time_left").innerHTML = opp_time_left;
    game = new Chess(fen);
    //updateGameLog();
});


function onDragStart (source, piece, position, orientation) {
    if (!live 
        || !isTurn()
        || game.isGameOver()
        || (game.turn() === 'w' && piece.search(/^b/) !== -1)
        || (game.turn() === 'b' && piece.search(/^w/) !== -1))
        return false
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
      return 'snapback';
    }

    //socket.emit("make_move", )

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