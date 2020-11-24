$(document).ready(function() {

    var writeMessage;
    // building message element and appending to the list of all messages
    writeMessage = function(message) {
        this.text = message.text, this.side = message.side;
        this.write = function(localthis) {
            return function (e) {
                var today = new Date()
                //  time of the message sent
                var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
                // ul of all messaged to which the new one will be appended
                var messagesList = $('#chat_content').contents();
                // building the message element with user message
                var msgElement = '<li class="mar-btm"><div class="media-body pad-hor speech-right">'
                + '<div class="speech"><p class="media-heading">You</p>' 
                + localthis.text
                + '<p class="speech-time"><i class="fa fa-clock-o fa-fw"></i>'
                + time
                + '</p></div></div></li>';
                // appending the new message to list of all
                messagesList.append(msgElement);
                $('#chat_content').html(messagesList);
            };
        }(this); // Call write() with the message
        return this;
    }

    // Always active func, for writing message to UI and sending AJAX to back-end
    $(function () {
        var getMessageText, sendMessage;
        // Get the text of the user message
        getMessageText = function () {
            var $message_input;
            $message_input = $('#user_input');
            return $message_input.val();
        };

        sendMessage = function (text) {
            var $messages;
            var messageObject = new writeMessage({
                text : text,
                side : 'right'
            })
            // Check if msg is empty, don't display anything
            if (text.trim() === '') {
                return;
            };
            $messages = $('.messages_list');
            $('#user_input').val('');
            // write the message to UI
            messageObject.write(text);
            // scroll to bottom of message list
            return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
        };

        // Call AJAX to send message to back-end
        $('.send_message').click(function (e) {
            console.log("Making a AJAX call");
            e.preventDefault();
            sendInputData(getMessageText());
            sendMessage(getMessageText());
        });

        // On "Enter", get the message and display it to UI
        $('#user_input').keyup(function (e) {
            if (e.which === 13) {
                sendInputData(getMessageText());
                return sendMessage(getMessageText());
            }
        });
    });

    // AJAX call to back-end
    sendInputData = function (user_message) {
        var messageObject = new writeMessage({
            text : '',
            side : 'left'
        })
        // request to the backend
        $.ajax({
            type: 'POST',
            url: '/chat',
            datatype:"json",
            data: {"user_input" : user_message},
            success: function(output){
                messageObject.text = output;
                if (user_message) {
                    messageObject.write(output);
                }
            },
            error: function(e){
                console.log("Unable to send data to backend! " + e)
            }
        })
        console.log("User has written: " + user_message)
    }
});