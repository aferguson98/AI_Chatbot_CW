import datetime
import os
import sys

from flask import Flask, jsonify, render_template, request

from akobot import StationNotFoundError
from akobot.Chat import Chat

app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)
this_chat = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat')
def chat():
    return render_template('chatbot_ui.html')


@app.route('/chat', methods=["POST"])
def process_user_input():
    global this_chat

    user_input = request.form['user_input']
    is_system = request.form['is_system']

    if user_input == "":
        response = ("Hi! I'm AKOBot, a kind of bot that can help you travel by "
                    "train smarter. How can I be of assistance today?")
        this_chat = Chat()
        this_chat.add_message("bot", response, datetime.datetime.now())
        suggestions = ['Book a ticket', 'Delay prediction', 'Help & Support']
        response_req = True
    elif user_input == "POPMSG" and is_system == "true":
        message = this_chat.pop_message()
        response = message[0]
        suggestions = message[1]
        response_req = message[2]
    else:
        try:
            message = this_chat.add_message("human",
                                            user_input,
                                            datetime.datetime.now())
        except StationNotFoundError as e:
            print(e)
            message = ["Sorry! There has been an issue with this chat, please "
                       "reload the page to start a new chat.", ["Reload Page"],
                       True]
        response = message[0]
        suggestions = message[1]
        response_req = message[2]
    print(response, suggestions, response_req)
    return jsonify({"message": response,
                    "suggestions": suggestions,
                    "response_req": response_req})


if __name__ == '__main__':
    # If there's any arg then we're deploying over the web
    if len(sys.argv) > 1:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    # Otherwise, it's a local deployment
    else:
        app.run()
