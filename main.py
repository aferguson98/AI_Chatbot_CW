import datetime

from flask import Flask, jsonify, render_template, request

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
    if user_input == "":
        response = ("Hi! I'm AKOBot, a kind of bot that can help you travel by "
                    "train smarter. How can I be of assistance today?")
        this_chat = Chat()
        this_chat.add_message("bot", response, datetime.datetime.now())
        suggestions = ['Book a ticket', 'Delay Prediction', 'Help & Support']
    else:
        try:
            message = this_chat.add_message("human",
                                            user_input,
                                            datetime.datetime.now())
        except Exception as e:
            print(e)
            message = ["Sorry! There has been an issue with this chat, please "
                       "reload the page to start a new chat.", ["Reload Page"]]
        response = message[0]
        suggestions = message[1]
    return jsonify({"message": response, "suggestions": suggestions})


if __name__ == '__main__':
    app.run()
