let tag_message = "";
let urlCounter;
let complete_journey = []
let executed = false;
let complete = false;
let tag_req_map = {
    "DEP": "{FROM}",
    "ARR": "{TO}",
    "DDT": "{TAG:DAT}",
    "RET": "{TAG:RET}",
    "RTD": "{TAG:RAT}",
    "ADT": "{TAG:ADT}",
    "CHD": "{TAG:CHD}"
}

// When doc.ready
$(function () {

    urlCounter = 0;
    sendInputData("", true);

    // Call AJAX to send message to back-end
    $('#message_form').submit(function (e) {
        console.log("Making a AJAX call");
        e.preventDefault();
        let message = getMessageText();
        sendInputData(tag_message + " " + message);
        sendMessage(message);
    });

});

// Get the text of the user message
function getMessageText() {
    return $('#user_input').val();
}

// write user message
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
    let msgElement = `<div class="message bot typing"><span class="icon"></span><span class="content">
                      <div class="bubble"></div><div class="bubble"></div><div class="bubble"></div></span></div>`;
    $('#chat').append(msgElement);
}

// AJAX call to back-end
function sendInputData(user_message, isFirst=false, isSystem="false") {
    tag_message = "";
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
        data: {"user_input" : user_message, "is_system": isSystem},
        success: function(output){
            $(".typing").remove();
            messageObject.text = output.message;
            messageObject.suggestions = output.suggestions;
            messageObject.response_req = output.response_req;
            messageObject.write(output);
            changeUIFromTags(output.message, new Date().toTimeString().slice(0, 5));
            completeDelayPrediction(output.message);
            getControlTags(output.message);
            synthesizeSpeech(output.message.replace(/\s?\{[^}]+\}/g, ''));
            if(messageObject.text.includes("Ok great, let's get your booking started!") &&
               $(window).width() > 1400){
                $('main').css('width', 'calc(100% - 400px)');
                $('.side-bar').css("transform", "scaleX(1)");
                $('.content.active').slideUp(500);
                $('.content.inactive').slideUp(500);
                $('#booking .active').delay(500).slideDown(500);
                $('#predict .inactive').delay(500).slideDown(500);
                $('#support .inactive').delay(500).slideDown(500);
            }
            if(messageObject.text.includes("{REQ:DEP}")){
                navigator.geolocation.getCurrentPosition(getNearestStations);
            }
            if(messageObject.response_req === false){
                sendInputData("POPMSG", false, "true");
            }
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
    this.response_req = message.response_req;
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
            // remove any tags added by bot for UI display
            let cleanText = localthis.text.replace(/\s?\{[^}]+\}/g, '')
            // building the message element with user message
            let msgElement = `<div class="message ${author}"><span class="icon">
                </span><span class="content">${cleanText}
                <span class="time">${time}</span></span></div>`;
            // append suggestions if exist
            if(localthis.suggestions.length > 0) {
                msgElement += `<div class="suggestions-container">`;
                localthis.suggestions.forEach((suggestion) => {
                    if(suggestion === "Reload Page" || suggestion === "Start a new chat") {
                        msgElement += `<div class="suggestion"
                                       onclick="window.location.reload()">
                                  ${suggestion}</div>`
                    }else if(suggestion.includes("{BOOK:")){
                        let suggestionClean = suggestion.replace(/\s?\{[^}]+\}/g, '');
                        let url = suggestion.replace("{BOOK:", "").split("}")[0];
                        msgElement += `<div class="suggestion"
                                       onclick="openURL('${url}');">
                                  ${suggestionClean}</div>`
                    }else{
                        // removes non-human readable portion of suggestions
                        let suggestionClean = suggestion.replace(/\s?\{[^}]+\}/g, '')
                        
                        msgElement += `<div class="suggestion" 
                                       onclick="sendInputData('${suggestion}');
                                                sendMessage('${suggestionClean}');">
                                  ${suggestionClean}</div>`
                    }
                });
                msgElement += `</div>`;
            }
            // appending the new message to list of all
            $('#chat').append(msgElement);
        };
    }(this); // Call write() with the message
    return this;
}

function synthesizeSpeech(text) {
    let sdk = SpeechSDK
    let ssml = `<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="en-GB">
                <voice name="en-GB-RyanNeural">${text.replace("AKOBot", "akobot")}</voice></speak>`

    const speechConfig = sdk.SpeechConfig.fromSubscription("be0b6d81b60844a084339d50a0b79832",
                                                     "uksouth");
    const audioConfig = sdk.AudioConfig.fromDefaultSpeakerOutput();

    const synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);
    synthesizer.speakSsmlAsync(
        ssml,
        result => {
            if (result) {
                console.log(JSON.stringify(result));
            }
            synthesizer.close();
        },
        error => {
            console.log(error);
            synthesizer.close();
        });
}

function updateTicketField(tag, value, time){
     $('.' + tag).text(value.toUpperCase());
     $('#search-time').text(time)
}

function changeUIFromTags(messageText, updatedTime){
    let regex = new RegExp('{([^}]+)}', 'g');
    let results = [...messageText.matchAll(regex)]
    results.forEach(function(element){
        let tagArr = element[1].split(":");
        let tag = tagArr[0], value = tagArr[1];
        
        switch (tag){
            case 'DEP':
                updateTicketField('from', value, updatedTime)
                break;
            case 'ARR':
                updateTicketField('to', value, updatedTime)
                break;
            case 'DTM':
                updateTicketField('out', value.replace("_", ":"), updatedTime)
                break;
            case 'RTM':
                updateTicketField('in', value.replace("_", ":"), updatedTime)
                break;
            case 'RET':
                updateTicketField('ticket-header', value, updatedTime)
                break;
            case 'ADT':
                updateTicketField('adults', value, updatedTime)
                break;
            case 'CHD':
                updateTicketField('child', value, updatedTime)
                break;
            case 'COMP':
                sendInputData("RUN_ENGINE");
                complete = true;
                break;
            default:
                break;
       }
    });
}

function getControlTags(messageText){
    let regex = new RegExp('{([^}]+)}', 'g');
    let results = [...messageText.matchAll(regex)]
    results.forEach(function(element){
        let tagArr = element[1].split(":");
        let tag = tagArr[0], value = tagArr[1];
        switch (tag){
            case 'REQ':
                //The Reasoner has made a request of the user - the following message will need the matching tag code
                
                tag_message += tag_req_map[value];
                break;
            default:
                break;
        }
    });
}

function getNearestStations(latlng){
    let app_id = "e229607b";
    let app_key = "4ddd3f57cd0074f8cdd69b89454f81ef";
    let counter = 0;
    let lat = latlng.coords.latitude;
    let lng = latlng.coords.longitude;
    let suggestion_container = `<div class="suggestions-container">`;
    let url = "https://transportapi.com/v3/uk/places.json";
    $.ajax({
            type: "GET",
            url: `${url}?app_id=${app_id}&app_key=${app_key}&lat=${lat}&lon=${lng}&type=train_station`,
            datatype: "JSON",
            success: function (output) {
                output.member.forEach(function (elem) {
                    if (counter < 3) {
                        suggestion_container += `<div class="suggestion" 
                                                 onclick="sendInputData('{TAG:DEP}${elem.name}');
                                                 sendMessage('${elem.name}');">${elem.name}</div>`
                        counter++;
                    }
                });
                $('#chat').append(suggestion_container + "</div>");
            }
        }
    )
}

function openURL(url) {
  let tab = window.open(url, '_blank');
  tab.focus();
  if(urlCounter === 0){
      sendInputData("POPMSG", false, "true");
  }
  urlCounter++;
}

function completeDelayPrediction(msg){
    let regex = new RegExp('{([^}]+)}', 'g');
    let results = [...msg.matchAll(regex)];
    results.forEach(function(element){
        let tagArr = element[1].split(":");
        let tag = tagArr[0]
        complete_journey.push(tag)
    });
    if (complete_journey.includes("DEP") && complete_journey.includes("ARR") 
                    && complete_journey.includes("DLY")) {
            if (!executed){
                executed = true;
                sendInputData("RUN_ENGINE");
            }
        }
}
