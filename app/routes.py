from flask import render_template
from app import app

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template('index.html', title="welcome")