import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

const socket = io("/game");

socket.on('connect', () => {
    console.log("connected to chess game");
    socket.emit('join'); 
});

let board = Chessboard('board1', 'start');

$(window).resize(board.resize);

});