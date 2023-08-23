# ChessKey

# Table of Contents

1. [Project Overview](#description)
2. [Technologies Used](#techused)
3. [Credits](#credits)
4. [Usage](#usage)

## Project Overview <a name = "description"></a>
![ChessKey](/static/images/chesskey.jpeg)

ChessKey is a web application I created to solve an issue myself and many of my chess-addicted friends had: the ability to quickly create a shareable link to a chess game without the need to login to any of the popular chess sites. That's exactly what ChessKey is! Similar to yellkey.com, ChessKey allows users to create a short and shareable link which initializes a chess match with whoever visits the link first. Features include the ability to customize the chess match by choosing their starting side and time controls, as well as a live chat.

![ChessKey Live Demo](/static/images/chesskeydemo.gif)

## Technologies Used <a name = "techused"></a>

The backend for this app is written in Python using `Flask`. Communication between the users and server is implemented using WebSockets (`flask-socketio`). The frontend is written in `Vanilla JS/HTML/CSS`. Relevant match data is stored in a `PostgreSQL` database.  

## Credits <a name = "credits></a>

## Usage <a name = "usage"></a>

PRs accepted.
