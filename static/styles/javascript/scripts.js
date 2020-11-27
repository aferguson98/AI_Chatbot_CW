// When doc.ready 
$(function () {
    sendInputData("", true)

    // Call AJAX to send message to back-end
    $('#message_form').submit(function (e) {
        console.log("Making a AJAX call");
        e.preventDefault();
        sendInputData(getMessageText());
        sendMessage(getMessageText());
    });

});

// Get the text of the user message
function getMessageText() {
    return $('#user_input').val();
}

// write user mesasge 
function sendMessage(text) {
    if($('.suggestions-container').length){
        $('.suggestions-container').fadeOut(500);
    }
    let messageObject = new writeMessage({
        text: text,
        side: 'right',
        suggestions: []
    });
    // Check if message is empty, don't display anything
    if (text.trim() === '') {
        return;
    }
    $('#user_input').val('');
    // write the message to UI
    messageObject.write(text);
}

// AJAX call to back-end
function sendInputData(user_message, isFirst=false) {
    if (user_message.trim() === '' && !isFirst) {
        return;
    }
    let messageObject = new writeMessage({
        text: '',
        side: 'left',
        suggestions: []
    });
    // request to the backend
    $.ajax({
        type: 'POST',
        url: '/chat',
        datatype:"json",
        data: {"user_input" : user_message},
        success: function(output){
            messageObject.text = output.message;
            messageObject.suggestions = output.suggestions;
            messageObject.write(output);
        },
        error: function(e){
            console.error("Could not send to backend: " + e.statusText);
        }
    });
    console.log("User has written: " + user_message);
}

// building message element and appending to the list of all messages
function writeMessage(message) {
    this.text = message.text;
    this.side = message.side;
    this.suggestions = message.suggestions;
    let author;
    if(this.side === 'left'){
        author = "bot";
    } else {
        author = "human";
    }
    this.write = function(localthis) {
        return function (e) {
            let today = new Date();
            //  time of the message sent
            let time = today.toTimeString().slice(0, 5);
            // building the message element with user message
            let msgElement = `<div class="message ${author}"><span class="icon">
                </span><span class="content">${localthis.text}
                <span class="time">${time}</span></span></div>`;
            // append suggestions if exist
            if(localthis.suggestions.length > 0) {
                msgElement += `<div class="suggestions-container">`;
                localthis.suggestions.forEach((suggestion) => {
                   msgElement += `<div class="suggestion" 
                                       onclick="sendInputData('${suggestion}');
                                                sendMessage('${suggestion}');">
                                  ${suggestion}</div>`
                });
                msgElement += `</div>`;
            }
            // appending the new message to list of all
            $('#chat').append(msgElement);
        };
    }(this); // Call write() with the message
    return this;
}