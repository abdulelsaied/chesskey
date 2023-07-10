import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

    if (document.getElementById("usernameButton").value == "False") {
    
      const socket = io();
      const username = document.querySelector('#username').getAttribute('data-value');
      const room = document.querySelector('#room').getAttribute('data-value');
      let side = document.querySelector('#side').getAttribute('data-value');
      let time_control = parseInt(document.querySelector('#time_control').getAttribute('data-value')) * 60; // convert starting time to seconds
      let opp_time_control = parseInt(document.querySelector('#time_control').getAttribute('data-value')) * 60; // convert starting time to seconds
      let score = 0;
      let opp_score = 0;
      let increment = parseInt(document.querySelector('#increment').getAttribute('data-value')); // increment already in seconds
      let game = new Chess();
      const config = {
        draggable: true,
        position: 'start',
        showErrors: 'console',
        onDragStart: onDragStart,
        onDrop: onDrop,
        onSnapEnd: onSnapEnd,
        dropOffBoard: 'snapback'
      };
      let board = Chessboard('myBoard', config);

      socket.on('initialize', () => {

      });

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
        if (data['username'] == username) {
          document.querySelector('#opp_username').innerHTML = data['opp_username'];
          document.querySelector('#opp_time_left').innerHTML = opp_time_control;
          document.querySelector('#host_username').innerHTML = data['username'];
          document.querySelector('#time_left').innerHTML = time_control;
        } else {
          document.querySelector('#opp_username').innerHTML = data['username'];
        }
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

        // add move to game log
        var p = document.createElement('p');
        p.style.flex = "50%";
        var gamelog = document.querySelector('#display-gamelog-section')
        if (gamelog.children.length % 2 == 0) {
          p.innerHTML = (Math.floor(gamelog.children.length / 2) + 1).toString() + ". ";
        }
        p.innerHTML += data['target'];
        document.querySelector('#display-gamelog-section').append(p)
        checkGameOver();
      });
      
      function onDragStart (source, piece, position, orientation) {
        if (game.isGameOver()) return false
      
        if ((game.turn() === 'w' && piece.search(/^b/) !== -1) || // add extra checks that side matches the piece moving
            (game.turn() === 'b' && piece.search(/^w/) !== -1) || 
            isTurn()) {
          return false
        }
      }
      
      function onDrop (source, target) {
        try {
          var move = game.move({
            from: source,
            to: target,
            promotion: 'q' 
          });
        }
        catch (err) {
          console.log(err);
          return 'snapback';
        }
        socket.emit('update', {"fen": game.fen(), "room": room, "target": target});
      }

      function onSnapEnd() {
        board.position(game.fen());
      }

      function isTurn() {
        if ((game.turn() == "w" && side == "white") || (game.turn() == "b" && side == "black")) return true
        return false;
      }

      function checkGameOver() {
        if (game.isGameOver()) {
          if (game.isCheckmate()) {
            if (isTurn()) {
              document.getElementById("gameOverModalTitle").innerHTML = "You Lost!";
              document.getElementById("gameOverModalSubtitle").innerHTML = "by checkmate";
              opp_score += 1;
            } else {
              document.getElementById("gameOverModalTitle").innerHTML = "You Won!";
              document.getElementById("gameOverModalSubtitle").innerHTML = "by checkmate";
              score += 1;
            }
          }
          else if (game.isStalemate()) {
            document.getElementById("gameOverModalTitle").innerHTML = "You Drew!";
            document.getElementById("gameOverModalSubtitle").innerHTML = "by stalemate";
            score += 0.5;
            opp_score += 0.5;
          }
          else if (game.isDraw()) {
            document.getElementById("gameOverModalTitle").innerHTML = "You Drew!";
            document.getElementById("gameOverModalSubtitle").innerHTML = "by insufficient material";
            score += 0.5;
            opp_score += 0.5;
          }
          document.getElementById("opp_score").innerHTML = opp_score;
          document.getElementById("score").innerHTML = score;
          document.getElementById("gameOverButton").click();
        }
      }
      $(window).resize(board.resize);
    }
})