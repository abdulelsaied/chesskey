import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

    var btn = document.getElementById("usernameButton");
    if (btn.value == "False") {
    
      const socket = io();
      const username = document.querySelector('#username').getAttribute('data-value');
      const room = document.querySelector('#lobby').getAttribute('data-value');
      const side = document.querySelector('#side').getAttribute('data-value');
      var board = null;
      var game = new Chess();
      var config = {
        draggable: true,
        position: 'start',
        showErrors: 'console',
        onDragStart: onDragStart,
        onDrop: onDrop
      };
      board = Chessboard('myBoard', config);

      socket.on('connect', () => {
          console.log("connected");
          socket.emit('join', {'username': username, 'room': room});
      });

      socket.on('disconnect', () => {
        console.log("disconnected");
        socket.emit('leave', {'username': username, 'room': room});
      });

      socket.on('incoming-status-msg', data => {
          if (data['msg']) {
              const p = document.createElement('p');
              p.innerHTML = "[" + data['time_stamp'] + "] " + data['msg']
              document.querySelector('#display-message-section').append(p);
          }
      });

      socket.on('update-ui', data => {
        if (document.querySelector('#opp_username').innerHTML == "Opponent") {
          document.querySelector('#opp_username').innerHTML = data['username'];
        } 
        else {
          document.querySelector('#opp_username').innerHTML = data['opp_username'];
          document.querySelector('#opp_time_left').innerHTML = data['time_control'];
          document.querySelector('#host_username').innerHTML = data['username'];
          document.querySelector('#time_left').innerHTML = data['time_control'];
        }
        console.log(side);
        board.orientation(side);
      });

      document.querySelector('#send_message').onclick = () => {
          socket.emit('incoming_msg', {'msg': document.querySelector('#user_message').value, 'username': username, 'room': room});
          document.querySelector('#user_message').value = '';
      }

      socket.on('message', data => {
          if (data['msg']){
              var p = document.createElement('p');
              p.innerHTML = "[" + data['time_stamp'] + "] " + data['username'] + ": " + data['msg'];
              document.querySelector('#display-message-section').append(p);
          }
      });

      socket.on('update-board', data => {
        console.log(data['fen']);
        game = new Chess(data['fen']);
        board.position(data['fen']);
        if (game.isGameOver()) {
              
        }
      });
      
      function onDragStart (source, piece, position, orientation) {
        if (game.isGameOver()) return false
      
        if ((game.turn() === 'w' && piece.search(/^b/) !== -1) || // add extra checks that side matches the piece moving
            (game.turn() === 'b' && piece.search(/^w/) !== -1) || 
            (game.turn() == 'w' && side == "black") ||
            (game.turn() == 'b' && side == "white")) {
          return false
        }
      }
      
      function onDrop (source, target) {
        var move = game.move({
          from: source,
          to: target,
          promotion: 'q' 
        })
        if (move === null) return 'snapback'
        // send move to both users
        socket.emit('update', {"fen": game.fen(), "room": room});
        console.log(source);
        console.log(target);
      }

      $(window).resize(board.resize)
    }
})