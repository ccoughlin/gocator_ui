"""gocator_ui.py - simple client-side UI for the handheld laser profiler project

Chris R. Coughlin (TRI/Austin, Inc.)
"""

from flask import Flask, flash, jsonify, render_template, request, url_for, redirect
import os.path
from models import gocator_model

BASEPATH = os.path.dirname(os.path.abspath(__file__))
# Output path for generated plots
OUTPUTIMAGEPATH = os.path.join(BASEPATH, 'static', 'img', 'scanResults.png')
# Output path for profile data
OUTPUTDATAPATH = os.path.join(BASEPATH, 'static', 'scanResults.csv')

app = Flask(__name__)
# TODO - replace secret key on deployment
app.secret_key = '\x96\x02\xd9\xd9q\xd25e\xf0\x83<\x90\xc1\xb8\xde\xa9\xaak\r\x81\x17c\xda\xfb'

model = gocator_model.GocatorModel()

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
    trigger_dict['type'] = request.form['triggertype']
    if trigger_dict['type'] == 'Encoder':
        trigger_dict['travel_threshold'] = request.form['travel_threshold']
        trigger_dict['trigger_direction'] = request.form['trigger_direction']
    elif trigger_dict['type'] == 'Time':
        trigger_dict['frame_rate'] = request.form['frame_rate']
    trigger_dict['enable_gate'] = request.form.get('use_gate', False)
    if model.set_configured_trigger(trigger_dict):
        flash("Configuration successful.")
    else:
        flash("Configuration failed.")
    return redirect(url_for('index'))

@app.route('/trigger', methods=['GET'])
def trigger():
    """View/edit current trigger config"""
    return render_template('trigger.html')

@app.route('/encoder_config', methods=['GET', 'POST'])
def encoder_config():
    """GET/POST current Gocator 20x0 encoder config (JSON)"""
    if request.method == 'GET':
        return jsonify(model.get_configured_encoder())
    encoder_dict = model.get_sane_encoder()
    encoder_dict['encoder_model'] = request.form.get('encoder_model', 'Make/model not specified')
    encoder_dict['encoder_resolution'] = request.form.get('encoder_resolution', 0)
    if model.set_configured_encoder(encoder_dict):
        flash("Configuration successful.")
    else:
        flash("Configuration failed.")
    return redirect(url_for('index'))

@app.route('/encoder', methods=['GET'])
def encoder():
    """View/edit current encoder config"""
    return render_template('encoder.html')

@app.route('/logs', methods=['GET'])
def logs():
    """Displays current output and error logs"""
    output_log, error_log = model.get_scanner_logs()
    return render_template('logs.html', output_log=output_log, error_log=error_log)

@app.route('/clearlogs', methods=['GET'])
def clearlogs():
    """Erases the current output and error logs"""
    model.clear_scanner_logs()
    flash("Logs cleared.")
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
    # TODO - refactor to skip returning plot and/or data if not set
    get_plot = request.form.get('get_plot', 'false').lower() == 'true'
    get_data = request.form.get('get_data', 'true').lower() == 'true'
    try:
        if os.path.exists(OUTPUTDATAPATH):
            os.remove(OUTPUTDATAPATH)
        if os.path.exists(OUTPUTIMAGEPATH):
            os.remove(OUTPUTIMAGEPATH)
    except WindowsError: # file in use
        pass
    except OSError: # couldn't delete file(s)
        pass
    response = {"scanning":model.start_scanner(OUTPUTDATAPATH)}
    return jsonify(response)

@app.route('/stopscan', methods=['POST'])
def stopscan():
    """Stops profiling.  Returns JSON data with URLs for the raw data and a PNG plot of same."""
    model.stop_scanner()
    model.profile(OUTPUTDATAPATH, OUTPUTIMAGEPATH)
    response = {"scanning":False,
                "image":url_for('static', filename='img/scanResults.png'),
                "data":url_for('static', filename='scanResults.csv')}
    return jsonify(response)

def main():
    # TODO - replace debugging on deployment
    #app.run(debug=True)
    app.run(host='0.0.0.0')

if __name__ == '__main__':
    main()
