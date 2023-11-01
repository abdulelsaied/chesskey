const socket = io('/chat');

socket.on('connect', () => {
    console.log("connected to chat room");
    socket.emit('join'); 
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