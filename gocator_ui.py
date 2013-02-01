"""gocator_ui.py - simple client-side UI for the handheld laser profiler project

Chris R. Coughlin (TRI/Austin, Inc.)
"""

from flask import Flask, flash, jsonify, render_template, request, url_for, redirect
import os.path

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
