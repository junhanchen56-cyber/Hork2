from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello! Vercel is working!"

@app.route('/test')
def test():
    return "Test route working!"
