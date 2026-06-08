from flask import Flask, send_from_directory
import threading
import bot  # Bu bot.py faylingni chaqiradi

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# Botni fon rejimida yurgizish
if __name__ == "__main__":
    threading.Thread(target=bot.bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=10000)
