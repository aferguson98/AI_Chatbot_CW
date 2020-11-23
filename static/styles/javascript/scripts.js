$(document).ready(function() {

    // building message element and appending to the list of all messages
    write = function(message) {
        return function () {
            var today = new Date()
            //  time of the message sent
            var time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds()
            // ul of all messaged to which the new one will be appended
            var messagesList = $('list-unstyled media-block')
            // building the message element with user message
            var msgElement = '<li class="mar-btm"><div class="media-body pad-hor speech-right">'
            + '<div class="speech"><p class="media-heading">You</p>' 
            + message.text
            + '<p class="speech-time"><i class="fa fa-clock-o fa-fw"></i>'
            + time
            + '</p></div></div></li>'
            // appending the new message to list of all
            messagesList.append(msgElement)
        };
    }

    // Always active func, for writing message to UI and sending AJAX to back-end
    $(function () {
        var getMessageText, sendMessage;
        // Get the text of the user message
        getMessageText = function () {
            var $message_input;
            $message_input = $('.user_input');
            return $message_input.val();
        };

        sendMessage = function (text) {
            var $messages;
            // Check if msg is empty, don't display anything
            if (text.trim() === '') {
                return;
            }
            $('.user_input').val('');
            // write the message to UI
            write(text);
            // scroll to bottom of message list
            return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
        };

        // Call AJAX to send message to back-end
        $('.send_message').click(function () {
            sendInputData(getMessageText());
            return sendMessage(getMessageText());
        });

        // On "Enter", get the message and display it to UI
        $('.user_input').keyup(function (e) {
            if (e.which === 13) {
                sendInputData(getMessageText());
                return sendMessage(getMessageText());
            }
        });
    });

    // AJAX call to back-end
    sendInputData = function (user_message) {
        // request to the backend
        $.ajax({
            type: 'POST',
            url: '/chat',
            data: user_message,
            success: function(output){
                console.log(output);
                if (user_message) {
                    write(output);
                }
            },
            error: function(e){
                console.log("Unable to send data to backend! " + e)
            }
        })
        console.log(user_message)
    }
});