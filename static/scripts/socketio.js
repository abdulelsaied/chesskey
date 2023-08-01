import { Chess } from '../node_modules/chess.js/dist/chess.js'

document.addEventListener('DOMContentLoaded', () => {

    if (document.getElementById("usernameButton").value == "False") {
    
      const socket = io();

      // html-read values
      const username = document.querySelector('#username').getAttribute('data-value');
      const room = document.querySelector('#room').getAttribute('data-value');

      // db-read values
      let live = false;
      let side;
      let time_control;
      let increment;
      let move_log;
      let fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

      // client-saved values
      let score = 0;
      let opp_score = 0;
      let ping_connection;
      let pings = [];
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

      socket.on('connect', () => {
          console.log("connected");
          socket.emit('join');
      });

      socket.on('route-index', () => {
        routeToIndex();
      });

      socket.on('disconnect', () => {
        console.log("disconnected");
        //socket.emit('leave');
      });

      socket.on('incoming-status-msg', data => {
          if (data['msg']) {
              let p = document.createElement('p');
              p.innerHTML = "[" + data['time_stamp'] + "] " + data['msg']
              document.querySelector('#display-message-section').append(p);
          }
      });

      socket.on('receive-ping', ping => {
        pings.push(ping);
        console.log(pings)
        if (pings.length == 2 && pings[0] == true && pings[1] == true) {
          clearInterval(ping_connection);
          socket.emit('close_room');
        }
        if (pings.length > 1) {
          pings.shift(); // [False, True] -> [True]
        }
    });

      socket.on('update-ui', room_row => {
        // SHOULD CHECK GAME OVER AT THE END OF THIS FUNCTION TOO 
        updateDbValues(room_row);
        board.orientation(side);  
        console.log(fen);
        game = new Chess(fen);
        let moveArray = room_row['move_log'].split('/');
        moveArray.pop(); // remove empty entry at the end
        updateGameLog(moveArray);
        if (username == room_row['user1']) {
          if (room_row['user2']) {
            document.querySelector('#opp_username').innerHTML = room_row['user2'];
          } else {
            document.querySelector('#opp_username').innerHTML = "Opponent";
          }
        } else if (username == room_row['user2']) {
          document.querySelector('#opp_username').innerHTML = room_row['user1'];
        }  
        document.querySelector('#opp_time_left').innerHTML = time_control;
        document.querySelector('#host_username').innerHTML = username;
        document.querySelector('#time_left').innerHTML = time_control;
        if (fen != 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1') { // this stops new game from creating the right board
          board.position(fen);
        }
        if (live){
          ping_connection = setInterval(pingConnection, 10000);
        }
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
        game.load(data['fen']);
        board.position(game.fen());
        updateGameLog(data['move']);
        checkGameOver();
      });

      socket.on('send-draw-request', user => {
        console.log("adding draw buttons")
        console.log(user);
        if (user == username) {
          const game_buttons = document.getElementById('game-buttons');
          game_buttons.insertAdjacentHTML('beforeend', "<i id = 'draw-reject' class = 'lni lni-cross-circle' style = 'font-size: 1.5em'></i>");
          game_buttons.insertAdjacentHTML('beforeend', "<i id = 'draw-accept' class = 'lni lni-checkmark-circle' style = 'font-size: 1.5em'></i>");
          const draw_reject = document.getElementById('draw-reject');
          draw_reject.addEventListener("click", rejectDraw);
          const draw_accept = document.getElementById('draw-accept');
          draw_accept.addEventListener("click", acceptDraw);
        }
      });

      socket.on('send-resign-request', () => {
        console.log("adding resign buttons")
        console.log(username);
        const game_buttons = document.getElementById('game-buttons');
        game_buttons.insertAdjacentHTML('beforeend', "<i id = 'resign-reject' class = 'lni lni-cross-circle' style = 'font-size: 1.5em'></i>");
        game_buttons.insertAdjacentHTML('beforeend', "<i id = 'resign-accept' class = 'lni lni-checkmark-circle' style = 'font-size: 1.5em'></i>");
        const resign_reject = document.getElementById('resign-reject');
        resign_reject.addEventListener("click", rejectResign);
        const resign_accept = document.getElementById('resign-accept');
        resign_accept.addEventListener("click", acceptResign);
      });

      socket.on('send-rematch-request', user => {
        console.log("adding rematch buttons")
        console.log(user);
        if (user == username) {
          const game_buttons = document.getElementById('game-buttons');
          game_buttons.insertAdjacentHTML('beforeend', "<i id = 'rematch-reject' class = 'lni lni-cross-circle' style = 'font-size: 1.5em'></i>");
          game_buttons.insertAdjacentHTML('beforeend', "<i id = 'rematch-accept' class = 'lni lni-checkmark-circle' style = 'font-size: 1.5em'></i>");
          const rematch_reject = document.getElementById('rematch-reject');
          rematch_reject.addEventListener("click", rejectRematch);
          const rematch_accept = document.getElementById('rematch-accept');
          rematch_accept.addEventListener("click", acceptRematch);
        }
      });

      function acceptRematch() {
        socket.emit('rematch_result', true);
      }

      function rejectRematch() {
        socket.emit('rematch_result', false);
      }

      function acceptResign() {
        socket.emit('resign_result', true);
      }

      function rejectResign() {
        socket.emit('resign_result', false);
      }

      socket.on('trigger-draw', draw => {
        const game_buttons = document.getElementById('game-buttons');
        if (document.getElementById('draw-reject')) {
          game_buttons.removeChild(document.getElementById('draw-reject'));
          game_buttons.removeChild(document.getElementById('draw-accept'));
        }
        if (draw) {
          // trigger modal with draw
          live = false;
          document.getElementById("gameOverModalTitle").innerHTML = "You Drew!";
          document.getElementById("gameOverModalSubtitle").innerHTML = "by agreement";
          score += 0.5;
          opp_score += 0.5;
          document.getElementById("opp_score").innerHTML = opp_score;
          document.getElementById("score").innerHTML = score;
          game_buttons.insertAdjacentHTML("beforeend", "<i id = 'rematch' class = 'lni lni-spinner-arrow' style = 'font-size: 1.5em'></i>");
          document.getElementById("rematch").addEventListener("click", requestRematch);
          document.getElementById("gameOverButton").click();
        }
      });


      socket.on('trigger-rematch', rematch => {
        const game_buttons = document.getElementById('game-buttons');
        if (document.getElementById('rematch-reject')) {
          game_buttons.removeChild(document.getElementById('rematch-reject'));
          game_buttons.removeChild(document.getElementById('rematch-accept'));
        } 
        if (rematch) {
          newGame();
        }
      });

      socket.on('trigger-resign', data => {
        const game_buttons = document.getElementById('game-buttons');
        if (data['resign']) {
          // trigger modal with draw
          live = false;
          if (data['user'] == username) {
            game_buttons.removeChild(document.getElementById('resign-reject'));
            game_buttons.removeChild(document.getElementById('resign-accept'));
            document.getElementById("gameOverModalTitle").innerHTML = "You Lost!";
            opp_score += 1.0;
          } else {
            document.getElementById("gameOverModalTitle").innerHTML = "You Won!";
            score += 1.0;
          }
          document.getElementById("gameOverModalSubtitle").innerHTML = "by resignation";
          document.getElementById("opp_score").innerHTML = opp_score;
          document.getElementById("score").innerHTML = score;
          game_buttons.insertAdjacentHTML("beforeend", "<i id = 'rematch' class = 'lni lni-spinner-arrow' style = 'font-size: 1.5em'></i>");
          document.getElementById("rematch").addEventListener("click", requestRematch);
          document.getElementById("gameOverButton").click();
        }
      });

      function rejectDraw() {
        socket.emit('draw_result', false);
      }

      function acceptDraw() {
        socket.emit('draw_result', true);
      }


      // ADD ALL THESE BUTTONS ONCE GAME IS LIVE 

      const home = document.getElementsByClassName("route-home");
      for (let homeButton of home) {
        homeButton.addEventListener("click", routeToIndex);
      }

      const resign = document.getElementById("resign");
      resign.addEventListener("click", triggerResign);

      const draw = document.getElementById("draw");
      draw.addEventListener("click", requestDraw);

      function triggerResign() {
        console.log("requesting resign");
        socket.emit('request_resign');
      }

      function requestRematch() {
        console.log("requesting rematch");
        socket.emit('request_rematch', document.querySelector('#opp_username').innerHTML);
      }

      function requestDraw() {
        console.log("requesting draw");
        socket.emit('request_draw', document.querySelector('#opp_username').innerHTML);
      }

      function newGame() {
        console.log("initializing new game");
        socket.emit('new_game');
      }

      function updateGameLog(moveArray) { // takes in an array of moves 
        // dont want to update game log when there are already items in the game log, in which case 
        // when game log has the same number of items as the movelog, than its up to date --> dont add new movelog items to it
        
        // if moveArray empty, clear game log?
        let gameLog = document.querySelector('#display-gamelog-section');
        if (moveArray.length == gameLog.children.length && moveArray.length != 1) {
          return;
        }
        if (moveArray.length == 0) {
          gameLog.innerHTML = '';
        }
        for (let move of moveArray) {
          if (move) {
            let p = document.createElement('p');
            p.style.flex = "50%";
            if (gameLog.children.length % 2 == 0) {
              p.innerHTML = (Math.floor(gameLog.children.length / 2) + 1).toString() + ". ";
            }
            p.innerHTML += move;
            gameLog.append(p);
          }
        }
      } 
      
      function onDragStart (source, piece, position, orientation) {
        if (!live || game.isGameOver()) return false
      
        if ((game.turn() === 'w' && piece.search(/^b/) !== -1) || // add extra checks that side matches the piece moving
            (game.turn() === 'b' && piece.search(/^w/) !== -1) || 
            !isTurn()) {
          return false;
        }
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
        // set fen and move log in db
        let move = game.history().slice(-1);
        socket.emit('update', {"fen": game.fen(), "room": room, "move": move});
      }

      function onSnapEnd() {
        board.position(game.fen());
      }

      function pingConnection() {
        socket.emit('check_connection');
      }

      function isTurn() {
        if ((game.turn() == "w" && side == "white") || (game.turn() == "b" && side == "black")) return true
        return false;
      }

      function routeToIndex() {
        let data = new FormData();
        data.append("msg", "index");
        fetch(window.location, {
          "method": "POST",
          "body": data
        }).then((response) => {
          if (response.redirected) {
            window.location.href = response.url;
          }
        });
      }

      function updateDbValues(room_row) {
        live = room_row['live'];
        if (username == room_row['user1']) {
          side = room_row['user1_side'];
        } else if (username == room_row['user2']) {
          side = room_row['user2_side'];
        }
        time_control = room_row['time_control'];
        increment = room_row['increment'];
        move_log = room_row['move_log']
        fen = room_row['fen']
      }

      function checkGameOver() {
        if (game.isGameOver()) {
          live = false;
          // SET LIVE TO FALSE IN THE DB?
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