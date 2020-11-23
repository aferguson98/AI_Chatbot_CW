from flask import Flask, render_template
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
    response = "HEEEEEEEEEEELO AJAX!"
    print("User input received... ")
    return response

if __name__ == '__main__':
    app.run()