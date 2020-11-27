from flask import Flask, jsonify, render_template, request
from akobot.AKOBot import NLPEngine

app = Flask(__name__, template_folder='templates')
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)


@app.route('/chat')
def chat():
    return render_template('chatbot_ui.html')


@app.route('/chat', methods=["POST"])
def process_user_input():
    user_input = request.form['user_input']
    if user_input == "":
        response = ("Hi! I'm AKOBot, a kind of bot that can help you travel by "
                    "train smarter. How can I be of assistance today?")
        suggestions = ['Book a ticket', 'Delay Prediction', 'Help & Support']
    else:
        eng = NLPEngine()
        print("Input received in main.py", user_input)
        eng.process(user_input)
        response = "You said: " + user_input
        suggestions = ['Hmm']
    return jsonify({"message": response, "suggestions": suggestions})


if __name__ == '__main__':
    app.run()
