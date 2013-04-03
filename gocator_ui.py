#!/usr/bin/env python
"""gocator_ui.py - simple client-side UI for the handheld laser profiler project

Chris R. Coughlin (TRI/Austin, Inc.)
"""

from flask import Flask, flash, g, jsonify, render_template, request, session, url_for, redirect
import datetime
from functools import wraps
import json
import os.path
import os
import tempfile
from zipfile import ZipFile
from models import gocator_model

app = Flask(__name__)
app.config.from_object('config')
model = gocator_model.GocatorModel()

def temp_fname(fldr, ext):
    """Wrapper for generating a NamedTemporaryFile in the specified folder with the
    specified extension.  Caller responsible for deleting the file."""
    fname = tempfile.NamedTemporaryFile(dir=fldr, suffix=ext)
    return fname.name

def temp_data_fname():
    """Returns a temporary filename for data files"""
    return temp_fname(fldr=app.config['OUTPUTDATAPATH'], ext=".csv")

def temp_image_fname():
    """Returns a temporary filename for image files"""
    return temp_fname(fldr=app.config['OUTPUTIMAGEPATH'], ext=".png")

def list_data_files():
    """Returns a list of the CSV files currently on the controller"""
    return [fname for fname in os.listdir(app.config['OUTPUTDATAPATH']) if fname.endswith("csv")]

def list_plot_files():
    """Returns a list of the bitmap plot files currently on the controller"""
    return [fname for fname in os.listdir(app.config['OUTPUTIMAGEPATH']) if fname.endswith("png")]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in', None) is None:
            flash("Login required", "error")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main entry page for the Hole Quality Scanner"""
    return render_template('index.html')

@app.route('/trigger_config', methods=['GET', 'POST'])
def trigger_config():
    """GET/POST current Gocator 20x0 trigger config (JSON)"""
    if request.method == 'GET':
        return jsonify(model.get_configured_trigger())
    trigger_dict = model.get_sane_trigger()
    if not request.content_type == 'application/json':
        trig_cfg = request.form
    else:
        trig_cfg = json.loads(request.data)
    trigger_dict['type'] = trig_cfg['triggertype']
    if trigger_dict['type'] == 'Encoder':
        trigger_dict['travel_threshold'] = trig_cfg['travel_threshold']
        trigger_dict['travel_direction'] = trig_cfg['travel_direction']
    elif trigger_dict['type'] == 'Time':
        trigger_dict['frame_rate'] = trig_cfg['frame_rate']
    trigger_dict['enable_gate'] = trig_cfg.get('use_gate', False)
    if model.set_configured_trigger(trigger_dict):
        flash("Configuration successful", "success")
    else:
        flash("Configuration failed", "error")
    return url_for('index')

@app.route('/trigger', methods=['GET'])
@login_required
def trigger():
    """View/edit current trigger config"""
    return render_template('trigger.html')

@app.route('/encoder_config', methods=['GET', 'POST'])
def encoder_config():
    """GET/POST current Gocator 20x0 encoder config (JSON)"""
    if request.method == 'GET':
        return jsonify(model.get_configured_encoder())
    encoder_dict = model.get_sane_encoder()
    if not request.content_type == 'application/json':
        encoder_cfg = request.form
    else:
        encoder_cfg = json.loads(request.data)
    encoder_dict['encoder_model'] = encoder_cfg.get('encoder_model', 'Make/model not specified')
    encoder_dict['encoder_resolution'] = encoder_cfg.get('encoder_resolution', 0)
    if model.set_configured_encoder(encoder_dict):
        flash("Configuration successful", "success")
    else:
        flash("Configuration failed", "failed")
    return url_for('index')

@app.route('/encoder', methods=['GET'])
@login_required
def encoder():
    """View/edit current encoder config"""
    return render_template('encoder.html')

@app.route('/logs', methods=['GET'])
def logs():
    """Displays current output and error logs"""
    output_log, error_log = model.get_scanner_logs()
    return render_template('logs.html', output_log=output_log, error_log=error_log)

@app.route('/clearlogs', methods=['GET'])
@login_required
def clearlogs():
    """Erases the current output and error logs"""
    model.clear_scanner_logs()
    flash("Logs cleared")
    return redirect(url_for('index'))

@app.route('/help', methods=['GET'])
def help():
    """Displays basic system help"""
    return render_template('help.html')

@app.route('/tri', methods=['GET'])
def tri():
    """Displays basic info about TRI"""
    return render_template('tri.html')

@app.route('/scan', methods=['POST'])
def scan():
    """Initiate profiling"""
    session['get_plot'] = request.form.get('get_plot', 'false').lower() 
    session['get_data'] = request.form.get('get_data', 'true').lower() 
    scan_comments = request.form.get('scan_comments', None)
    session['data_path'] = temp_data_fname()
    session['image_path'] = temp_image_fname()
    response = {"scanning":model.start_scanner(session['data_path'], scan_comments)}
    return jsonify(response)

@app.route('/stopscan', methods=['POST'])
def stopscan():
    """Stops profiling.  Returns JSON data with URLs for the raw data and a PNG plot of same."""
    try:
        model.stop_scanner()
        if session['get_plot'] == 'true':
            model.profile(session['data_path'], session['image_path'])
        response = {"scanning":False,
                    "image":url_for('static', filename='data/img/{0}'.format(os.path.basename(session['image_path']))),
                    "data":url_for('static', filename='data/{0}'.format(os.path.basename(session['data_path'])))}
    except IOError: # no data recorded
        response = {"scanning":False,
                    "error":"No profile data recorded"}
    finally:    
        return jsonify(response)

@app.route('/target', methods=['POST'])
def target():
    """Start the laser, allow user to align before taking actual measurements"""
    response = {"running":model.start_target()}
    return jsonify(response)

@app.route('/stoptarget', methods=['POST'])
def stoptarget():
    """Turns the laser off after targeting"""
    model.stop_scanner()
    response = {"running":False}
    return jsonify(response)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login"""
    error = None
    if request.method == 'POST':
        if request.form['user'] != app.config['USERNAME'] or request.form['pword'] != app.config['PASSWORD']:
            error = "Invalid login"
        else:
            session['logged_in'] = True
            flash("Login successful", "success")
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    """Handles user logout"""
    session.pop('logged_in', None)
    flash("Logout successful", "success")
    return redirect(url_for('index'))

@app.route('/data', methods=['GET'])
def data():
    """Generates list of stored scans"""
    data_files = list_data_files()
    table_data = []
    for data_file in data_files:
        file_path = os.path.join(app.config["OUTPUTDATAPATH"], data_file)
        mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        table_data.append((data_file, mod_date))
    return render_template('data.html', datafiles=table_data)

@app.route('/dnld_data', methods=['POST'])
def download_data():
    """Creates ZIP archive of all the data"""
    data_files = list_data_files()
    zip_fname = os.path.join(app.config['OUTPUTDATAPATH'], "scans.zip")
    with ZipFile(zip_fname, 'w') as output_zip:
        for data_file in data_files:
            file_path = os.path.join(app.config["OUTPUTDATAPATH"], data_file)
            output_zip.write(file_path, arcname=os.path.basename(file_path))
        response = {'url':os.path.relpath(zip_fname, app.config['BASEPATH'])}
        return jsonify(response)
    response = {'error':"Unable to create ZIP archive"}
    return jsonify(response)

@app.route('/cleardata', methods=['GET'])
@login_required
def cleardata():
    """Erases the data files"""
    data_files = list_data_files()
    plot_files = list_plot_files()
    try:
        for fname in data_files:
            os.remove(os.path.join(app.config['OUTPUTDATAPATH'], fname))
        for fname in plot_files:
            os.remove(os.path.join(app.config['OUTPUTIMAGEPATH'], fname))
        flash("Data Erased", "success")
    except OSError as err: #Couldn't remove files
        flash("Unable to remove data files: {0}".format(err), "failed")
    finally:
        return redirect(url_for('index'))

def main():
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
