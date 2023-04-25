import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

    var btn = document.getElementById("usernameButton");
    if (btn.value == "False") {
    
      const socket = io();
      const username = document.querySelector('#username').getAttribute('data-value');
      const room = document.querySelector('#lobby').getAttribute('data-value');

      socket.on('connect', () => {
          console.log("connected");
          socket.emit('join', {'username': username, 'room': room});
      });

      // when a user disconnects, its crucial to delete the row from the database and alert the remaining player that the room is now closed
      socket.on('disconnect', () => {
        console.log("disconnected");
        // socket.emit('leave', {'username': username, 'room': room});
    });

      socket.on('incoming-status-msg', data => {
          if (data['msg']) {
              const p = document.createElement('p');
              p.innerHTML = "[" + data['time_stamp'] + "] " + data['msg']
              document.querySelector('#display-message-section').append(p);
          }
      });

      document.querySelector('#send_message').onclick = () => {
          socket.emit('incoming_msg', {'msg': document.querySelector('#user_message').value, 'username': username, 'room': room});
          document.querySelector('#user_message').value = '';
      }

      socket.on('message', data => {
          if (data['msg']){
              const p = document.createElement('p');
              const br = document.createElement('br');
              p.innerHTML = "[" + data['time_stamp'] + "] " + data['username'] + ": " + data['msg'];
              document.querySelector('#display-message-section').append(p);
          }
      });

      var board = null
      var game = new Chess()
      var $status = $('#status')
      var $fen = $('#fen')
      var $pgn = $('#pgn')
      
      function onDragStart (source, piece, position, orientation) {
        // do not pick up pieces if the game is over
        if (game.isGameOver()) return false
      
        // only pick up pieces for the side to move
        if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
            (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
          return false
        }
      }
      
      function onDrop (source, target) {
        // see if the move is legal
        var move = game.move({
          from: source,
          to: target,
          promotion: 'q' // NOTE: always promote to a queen for example simplicity
        })
      
        // illegal move
        if (move === null) return 'snapback'
      
        updateStatus()
      }
      
      // update the board position after the piece snap
      // for castling, en passant, pawn promotion
      function onSnapEnd () {
        board.position(game.fen())
      }
      
      function updateStatus () {
        var status = ''
      
        var moveColor = 'White'
        if (game.turn() === 'b') {
          moveColor = 'Black'
        }
      
        // checkmate?
        if (game.isCheckmate()) {
          status = 'Game over, ' + moveColor + ' is in checkmate.'
        }
      
        // draw?
        else if (game.isDraw()) {
          status = 'Game over, drawn position'
        }
      
        // game still on
        else {
          status = moveColor + ' to move'
      
          // check?
          if (game.inCheck()) {
            status += ', ' + moveColor + ' is in check'
          }
        }
      
        $status.html(status)
        $fen.html(game.fen())
        $pgn.html(game.pgn())
      }
      
      var config = {
        draggable: true,
        position: 'start',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd
      }

      board = Chessboard('myBoard', config)
      
      updateStatus()
    }
})