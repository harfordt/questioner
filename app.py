from flask import Flask, request, redirect, render_template, session
import os
from os import path

ROOT = path.dirname(path.realpath(__file__))

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
