const socket = io('/chat');

socket.on('connect', () => {
    console.log("connected to chat room");
    socket.emit('join'); 
});

let chatLog = document.getElementById("chat-box");

let chat_box = document.getElementById("user_message");
chat_box.addEventListener('keypress', function(event) {
    if (event.key == "Enter") {
        socket.emit("chat_msg", chat_box.value);
        chat_box.value = "";
    }
});

socket.on('chat-msg', msg => {
    if (msg){
        const p = document.createElement("p");
        p.classList.add('ml-2');
        p.innerText = msg;
        chatLog.appendChild(p);
        chatLog.scrollTop = chatLog.scrollHeight;
    }
});