const socket = io("/chat");

socket.on('connect', () => {
    console.log("connected to chat room");
    // socket.emit('join-chat'); 
    // if the user is user1, create the connection table and join session['room']
    // if the user is user2, update the connection table and join session['room']
    // also, create the gameinfo table and pass the information into an event that triggers the start of the game 
});

let chat_box = document.getElementById("user_message");
chat_box.addEventListener('keypress', function(event) {
    if (event.key == "Enter") {
        socket.emit("chat_msg", chat_box.value);
        chat_box.value = "";
    }
});

socket.on('chat-msg', data => {
    console.log("msg", data['msg']);
    if (data['msg']){
        const p = document.createElement("p");
        p.classList.add('odd:text-black', 'ml-4');
        p.innerText = "[" + data['time_stamp'] + "] " + data['msg'];
        document.getElementById("chat-box").appendChild(p);
    }
});