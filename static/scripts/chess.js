import { Chess } from "../node_modules/chess.js/dist/chess.js";

document.addEventListener("DOMContentLoaded", () => {
  const socket = io("/game");

  // TIMER VALUES
  let timer = new easytimer.Timer();
  let opp_timer = new easytimer.Timer();

  // HTML-READ VALUES
  let room = document.getElementById("room-data").getAttribute("data-value");
  let username = document
    .getElementById("username-data")
    .getAttribute("data-value");

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
    position: "start",
    showErrors: "console",
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    dropOffBoard: "snapback",
  };
  let board = Chessboard("board1", config);
  let game = new Chess();

  // ###################
  // # SOCKETIO EVENTS #
  // ###################

  socket.on("connect", () => {
    console.log("connected to chess game");
    document.getElementById("link").innerHTML = "thechesskey.com/" + room;
    document.getElementById("username").innerHTML = username;
    socket.emit("join");
  });

  socket.on("game-roominfo", (data) => {
    time_control = data["time_control"];
    increment = data["increment"];
    if (username == data["user1"]) {
      if (data["user2"] != null) {
        opp_username = data["user2"];
      } else {
        opp_username = "Opponent";
      }
      side = data["user1_side"];
      opp_side = data["user2_side"];
    } else {
      opp_username = data["user1"];
      side = data["user2_side"];
      opp_side = data["user1_side"];
    }
    document.getElementById("opp_username").innerHTML = opp_username;
    document.getElementById("scoreboard").innerHTML = username;
    document.getElementById("opp_scoreboard").innerHTML = opp_username;
    document.getElementById("time_left").innerHTML = time_control; // edit this to look like the easyTimer start value
    document.getElementById("opp_time_left").innerHTML = time_control;
    board.orientation(side);
    console.log(side);
  });

  // HERE IS WHERE DECIDE WHICH BUTTONS ARE DISPLAYED BASED ON CURRENT GAME STATE
  // ALSO CAN ADD MSG ABOUT OTHER USER DISCONNECTING IN THE FUTURE
  // DOES THIS GET CALLED FOR BOTH USERS WHEN USER2 JOINS THE MATCH FOR THE FIRST TIME?
  socket.on("game-connection", (data) => {
    console.log("Live: " + data["live"]);
    live = data["live"];

    if (live == "live") {
      console.log("did this");
      document
        .getElementById("draw-confirm")
        .addEventListener("mouseover", triggerDrawRequest);
      document
        .getElementById("resign-confirm")
        .addEventListener("mouseover", triggerResign);

      document.getElementById("draw-button").classList.remove("hidden");
      document.getElementById("resign-button").classList.remove("hidden");
      document.getElementById("rematch-button").classList.add("hidden");
      document.getElementById("newgame-button").classList.add("hidden");
    }

    if (live == "over") {
      document
        .getElementById("rematch-confirm")
        .addEventListener("mouseover", triggerRematchRequest);
      document
        .getElementById("newgame-confirm")
        .addEventListener("mouseover", triggerNewGame);

      document.getElementById("rematch-button").classList.remove("hidden");
      document.getElementById("newgame-button").classList.remove("hidden");
      document.getElementById("draw-button").classList.add("hidden");
      document.getElementById("resign-button").classList.add("hidden");

      // drew,
      let main_text;
      if (data["flag"] == 0) {
        main_text = "You drew!";
      } else {
        if (data["side"] == side) {
          main_text = "You Won!";
        } else {
          main_text = "You Lost!";
        }
      }

      document.getElementById("gameOverText").innerHTML = main_text;
      document.getElementById("gameOverSubtext").innerHTML = data["reason"];
      document.getElementById("modal-score").innerHTML = score;
      document.getElementById("modal-username").innerHTML = username;
      document.getElementById("opp-modal-score").innerHTML = opp_score;
      document.getElementById("opp-modal-username").innerHTML = opp_username;

      document.getElementById("gameOverButton").click();
    }
  });

  socket.on("game-gameinfo", (data) => {
    data = JSON.parse(data);
    console.log(data);
    fen = data["fen"];
    move_log = data["move_log"];
    game.load(data["fen"]);
    board.position(game.fen());
    updateGameLog();
    if (username == data["user1"]) {
      time_left = data["user1_time_left"];
      score = data["user1_score"];
      opp_time_left = data["user2_time_left"];
      opp_score = data["user2_score"];
    } else {
      time_left = data["user2_time_left"];
      score = data["user2_score"];
      opp_time_left = data["user1_time_left"];
      opp_score = data["user1_score"];
    }
    if (isTurn() && live == "live") {
      console.log(intervalToSeconds(time_left));
      timer.start({
        countdown: true,
        startValues: {
          seconds: intervalToSeconds(time_left) + parseInt(increment),
        },
      });
      opp_timer.start({
        countdown: true,
        startValues: {
          seconds: intervalToSeconds(opp_time_left) + parseInt(increment),
        },
      });
      opp_timer.stop();
    } else {
      console.log(intervalToSeconds(opp_time_left));
      timer.start({
        countdown: true,
        startValues: {
          seconds: intervalToSeconds(time_left) + parseInt(increment),
        },
      });
      opp_timer.start({
        countdown: true,
        startValues: {
          seconds: intervalToSeconds(opp_time_left) + parseInt(increment),
        },
      });
      timer.stop();
    }
    setTimers();
    document.getElementById("score").innerHTML = score;
    document.getElementById("opp_score").innerHTML = opp_score;

    console.log(fen);
    console.log(move_log);
    console.log(time_left);
    console.log(opp_time_left);
    console.log(score);
    console.log(opp_score);
  });

  socket.on("display-draw-request", (data) => {
    if (username == data["recipient"]) {
      let p = document.createElement("p");
      p.classList.add("ml-2");
      p.innerText = opp_username + " has requested a draw. Accept?";
      let chatLog = document.getElementById("chat-box");
      chatLog.appendChild(p);
      chatLog.innerHTML +=
        '<div class = "flex justify-start space-x-2"><button type = "button" id = "draw-accept" class = "bg-white text-black rounded-full border-black border-2 px-2 ml-2">Yes</button><button type = "button" id = "draw-reject" class = "bg-white text-black rounded-full border-black border-2 px-2">No</button></div>';
      chatLog.scrollTop = chatLog.scrollHeight;

      document
        .getElementById("draw-accept")
        .addEventListener("click", triggerDraw);
      document
        .getElementById("draw-reject")
        .addEventListener("click", triggerDrawReject);
    }
  });

  socket.on("display-rematch-request", (data) => {
    if (username == data["recipient"]) {
      let p = document.createElement("p");
      p.classList.add("ml-2");
      p.innerText = opp_username + " has requested a rematch. Accept?";
      let chatLog = document.getElementById("chat-box");
      chatLog.appendChild(p);
      chatLog.innerHTML +=
        '<div class = "flex justify-start space-x-2"><button type = "button" id = "rematch-accept" class = "bg-white text-black rounded-full border-black border-2 px-2 ml-2">Yes</button><button type = "button" id = "rematch-reject" class = "bg-white text-black rounded-full border-black border-2 px-2">No</button></div>';
      chatLog.scrollTop = chatLog.scrollHeight;

      document
        .getElementById("rematch-accept")
        .addEventListener("click", triggerRematch);
      document
        .getElementById("rematch-reject")
        .addEventListener("click", triggerRematchReject);
    }
  });

  socket.on("play-sound", (flag) => {
    let audioElement = new Audio();
    if (flag == "move") {
      audioElement = new Audio("./../static/audio/chess_piece_move.mp3");
    } else if (flag == "start") {
      audioElement = new Audio("./../static/audio/chess_game_start.mp3");
    } else if (flag == "over") {
      audioElement = new Audio("./../static/audio/chess_game_over.mp3");
    } else if (flag == "capture") {
      audioElement = new Audio("./../static/audio/chess_piece_capture.mp3");
    } else if (flag == "check") {
      audioElement = new Audio("./../static/audio/chess_check.mp3");
    } else if (flag == "castle") {
      audioElement = new Audio("./../static/audio/chess_castle.mp3");
    }
    audioElement.play();
  });

  // ###################
  // # HELPER FUNCTIONS #
  // ###################

  function triggerRematch() {
    console.log("triggering rematch accept");
    let chatLog = document.getElementById("chat-box");
    chatLog.removeChild(chatLog.lastChild);
    chatLog.removeChild(chatLog.lastChild);
    chatLog.scrollTop = chatLog.scrollHeight;

    socket.emit("new_game");
  }

  function triggerRematchReject() {
    console.log("triggering rematch deny");
    let chatLog = document.getElementById("chat-box");
    chatLog.removeChild(chatLog.lastChild);
    chatLog.removeChild(chatLog.lastChild);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function triggerDraw() {
    console.log("triggering draw");
    let chatLog = document.getElementById("chat-box");
    chatLog.removeChild(chatLog.lastChild);
    chatLog.removeChild(chatLog.lastChild);
    chatLog.scrollTop = chatLog.scrollHeight;

    socket.emit("game_over", { flag: 0, side: side, reason: "by agreement" });
  }

  function triggerDrawReject() {
    console.log("triggering draw deny");
    let chatLog = document.getElementById("chat-box");
    chatLog.removeChild(chatLog.lastChild);
    chatLog.removeChild(chatLog.lastChild);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function updateGameLog() {
    let moveArray = move_log.split("/");
    moveArray.pop();
    console.log(moveArray);
    let gameLog = document.getElementById("game-log");
    let gameLogLength = gameLog.children.length;

    if (moveArray.length == gameLogLength) {
      return;
    } else if (moveArray.length == 0) {
      gameLog.innerHTML = "";
    } else {
      for (let i = gameLogLength; i < moveArray.length; i++) {
        console.log(moveArray[i]);
        let p = document.createElement("p");
        if (i % 2 == 0) {
          p.classList.add("pl-2");
          p.innerHTML = (Math.floor(i / 2) + 1).toString() + ". ";
        }
        p.innerHTML += moveArray[i];
        gameLog.append(p);
      }
    }
    gameLog.scrollTop = gameLog.scrollHeight;
  }

  function checkGameOver() {
    if (game.isGameOver()) {
      stopTimers();
      // 0 = draw, 1 = {username} won
      let flag = 0;
      if (game.isCheckmate()) {
        flag = 1;
        socket.emit("game_over", {
          flag: flag,
          side: side,
          reason: "by checkmate",
        });
      } else {
        if (game.isInsufficientMaterial()) {
          socket.emit("game_over", {
            flag: flag,
            side: side,
            reason: "due to insufficient material",
          });
        } else if (game.isStalemate()) {
          socket.emit("game_over", {
            flag: flag,
            side: side,
            reason: "by stalemate",
          });
        } else if (game.isThreefoldRepetition()) {
          socket.emit("game_over", {
            flag: flag,
            side: side,
            reason: "by threefold repetition",
          });
        }
      }
    }
  }

  function triggerDrawRequest() {
    console.log("triggering draw");
    socket.emit("draw_request", { recipient: opp_username });
  }

  function triggerResign() {
    console.log("triggering resign");
    socket.emit("game_over", {
      flag: 1,
      side: opp_side,
      reason: "by resignation",
    });
  }

  function triggerRematchRequest() {
    console.log("triggering rematch");
    socket.emit("rematch_request", { recipient: opp_username });
  }

  function triggerNewGame() {
    console.log("triggering new game");
    routeToIndex();
  }

  function routeToIndex() {
    let data = new FormData();
    data.append("msg", "index");
    fetch(window.location, {
      method: "POST",
      body: data,
    }).then((response) => {
      if (response.redirected) {
        window.location.href = response.url;
      }
    });
  }

  function onDragStart(source, piece, position, orientation) {
    if (
      live != "live" ||
      !isTurn() ||
      game.isGameOver() ||
      (game.turn() === "w" && piece.search(/^b/) !== -1) ||
      (game.turn() === "b" && piece.search(/^w/) !== -1)
    ) {
      return false;
    }
    console.log("valid move");
  }

  function onDrop(source, target) {
    try {
      game.move({
        from: source,
        to: target,
        promotion: "q",
      });
    } catch (err) {
      console.log("error making move");
      return "snapback";
    }
    let move_string = game.history().slice(-1);
    socket.emit("make_move", {
      move: move_string,
      fen: game.fen(),
      user: username,
      increment: increment,
    });
    socket.emit("play_move_sound", move_string[0]);
    checkGameOver();
  }

  function onSnapEnd() {
    board.position(game.fen());
  }

  function isTurn() {
    if (
      (game.turn() == "w" && side == "white") ||
      (game.turn() == "b" && side == "black")
    )
      return true;
    return false;
  }

  // strip of milliseconds

  function beautifyTimeLeft(timeLeft) {
    try {
      return timeLeft.split(".")[0];
    } catch (error) {
      console.log(error);
      return timeLeft;
    }
  }

  function intervalToSeconds(timeLeft) {
    let fractionalSeconds = 0;
    let timeLeftArr = timeLeft.split(".");
    if (timeLeftArr.length > 1) {
      fractionalSeconds = parseInt(timeLeftArr[1]);
    }

    let rest = timeLeftArr[0].split(":");
    return (
      parseInt(rest[2]) +
      parseInt(rest[1]) * 60 +
      parseInt(rest[0]) * 3600 +
      fractionalSeconds / 1000000
    );
  }

  function setTimers() {
    timer.addEventListener("secondsUpdated", function (e) {
      $("#time_left").html(timer.getTimeValues().toString()); // BEAUTIFY THIS STRING HERE
    });
    opp_timer.addEventListener("secondsUpdated", function (e) {
      $("#opp_time_left").html(opp_timer.getTimeValues().toString());
    });

    timer.addEventListener("targetAchieved", function (e) {
      socket.emit("game_over", {
        flag: 1,
        side: opp_side,
        reason: "by timeout",
      });
      stopTimers();
    });
  }

  function stopTimers() {
    timer.stop();
    opp_timer.stop();
  }

  let link_elem = document.getElementById("link");
  link_elem.addEventListener("click", () => {
    navigator.clipboard.writeText(link_elem.innerText);
    document.getElementById("tooltip-link").innerHTML = "Copied!";
    setTimeout(function () {
      document.getElementById("tooltip-link").innerHTML = "Copy to clipboard";
    }, 5000);
  });

  $(window).resize(board.resize);
});
