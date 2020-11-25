from flask import Flask, render_template, request
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
    eng = NLPEngine()
    user_input = request.form['user_input']
    print("Input received in main.py", user_input)
    eng.process(user_input)
    response = "HEEEEEEEEEEELO AJAX!"
    return response

if __name__ == '__main__':
    app.run()