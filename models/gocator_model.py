"""gocator_model.py - handles the Gocator for the web UI

Chris R. Coughlin (TRI/Austin, Inc.)
"""

import os.path
import datetime
import subprocess

from configobj import ConfigObj
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.cm as cm
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def now_as_string():
    """Returns the current date and time as a string, suitable for use in timestamps or auto-generated
    filenames."""
    now = datetime.datetime.now()
    return now.strftime("%a%b%Y_%H%M")

def now_as_filename(basepath=None, file_extension=''):
    """Returns a filename based on the current date and time."""
    base_filename = now_as_string()
    if file_extension != '':
        base_filename = '.'.join([base_filename, file_extension])
    if basepath is not None:
        base_filename = os.path.join(basepath, base_filename)
    return base_filename

class GocatorModel(object):
    """Handles communications between UI and Gocator control app"""

    PROFILERPATH = "/home/ccoughlin/src/cxx/gocator_encoder"
    SCANNERPATH = os.path.join(PROFILERPATH, "gocator_encoder")
    ENCODERCONFIGPATH = os.path.join(PROFILERPATH, "gocator_encoder.cfg")
    STDOUTPATH = os.path.join(os.path.dirname(__file__), "profiler_output.log")
    STDERRPATH = os.path.join(os.path.dirname(__file__), "profiler_errors.log")

    def __init__(self, config_file):
        self.config_fname = config_file
        self.cfg = ConfigObj(self.config_fname)
        self.scanner_proc = None # subprocess used to run Gocator scanner

    @property
    def scanner_running(self):
        """Returns True if the scanner subprocess is running"""
        if self.scanner_proc is not None and self.scanner_proc.poll() is None:
            return True
        return False

    def get_sane_trigger(self):
        """Returns a dict of sane default settings for the Gocator trigger"""
        return {'type':'Encoder',
                'enable_gate':False,
                'frame_rate':300,
                'travel_threshold':1,
                'trigger_direction':'bidirectional'}

    def get_sane_encoder(self):
        """Returns a dict of sane default settings for the linear magnetic encoder"""
        return {'encoder_model':'unspecified', 'encoder_resolution':0}

    def get_configured_trigger(self):
        """Returns the trigger configuration"""
        trigger_dict = self.get_sane_trigger()
        if "Trigger" in self.cfg:
            trigger_config = self.cfg["Trigger"]
            if 'type' in trigger_config:
                acceptable_trigger_types = ['encoder', 'time', 'input']
                if trigger_config['type'].lower() in acceptable_trigger_types:
                    trigger_dict['type'] = trigger_config['type'].title()
            if 'enable_gate' in trigger_config:
                trigger_dict['enable_gate'] = trigger_config.as_bool('enable_gate')
            if 'frame_rate' in trigger_config:
                trigger_dict['frame_rate'] = trigger_config.as_int('frame_rate')
            if 'travel_threshold' in trigger_config:
                trigger_dict['travel_threshold'] = trigger_config.as_float('travel_threshold')
            if 'trigger_direction' in trigger_config:
                acceptable_directions = ['forward', 'backward', 'bidirectional']
                if trigger_config['trigger_direction'].lower() in acceptable_directions:
                    trigger_dict['trigger_direction'] = trigger_config['trigger_direction'].title()
        return trigger_dict

    def set_configured_trigger(self, new_trigger_config):
        """Saves the trigger configuration"""
        if 'Trigger' not in self.cfg:
            self.cfg['Trigger'] = {}
        trigger_config = self.cfg['Trigger']
        trigger_config['type'] = new_trigger_config['type']
        trigger_config['enable_gate'] = new_trigger_config['enable_gate']
        if 'frame_rate' in new_trigger_config:
            trigger_config['frame_rate'] = new_trigger_config['frame_rate']
        if 'travel_threshold' in new_trigger_config:
            trigger_config['travel_threshold'] = new_trigger_config['travel_threshold']
        if 'trigger_direction' in new_trigger_config:
            trigger_config['trigger_direction'] = new_trigger_config['trigger_direction']
        self.cfg.write()

    def get_configured_encoder(self):
        """Returns the encoder configuration"""
        lme = self.get_sane_encoder()
        if 'Encoder' in self.cfg:
            encoder_config = self.cfg['Encoder']
            if 'resolution' in encoder_config:
                lme['encoder_resolution'] = encoder_config.as_float('resolution')
            if 'model' in encoder_config:
                lme['encoder_model'] = encoder_config['model'].title()
        return lme

    def set_configured_encoder(self, new_encoder_config):
        """Saves the encoder configuration"""
        if 'Encoder' not in self.cfg:
            self.cfg['Encoder'] = {}
        encoder_config = self.cfg['Encoder']
        if 'encoder_model' in new_encoder_config:
            encoder_config['model'] = new_encoder_config['encoder_model']
        if 'encoder_resolution' in new_encoder_config:
            encoder_config['resolution'] = new_encoder_config['encoder_resolution']
        self.cfg.write()

    def start_scanner(self, output_file):
        """Starts the Gocator profiler, saves data to specified output file.
        Returns True if the scanning process was successfully started."""
        config_arg = "-c" + GocatorModel.ENCODERCONFIGPATH
        output_arg = "-o" + output_file
        self.scanner_proc = subprocess.Popen([GocatorModel.SCANNERPATH, config_arg, output_arg],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        return self.scanner_running

    def stop_scanner(self):
        """Stops the Gocator profiler, writes its stdout and stderr to log files"""
        if self.scanner_running:
            stdout = self.scanner_proc.stdout.read()
            stderr = self.scanner_proc.stderr.read()
            self.scanner_proc.stdin.write("q\n")
            with open(GocatorModel.STDOUTPATH, "ab") as stdout_fid:
                stdout_fid.write(stdout)
            with open(GocatorModel.STDERRPATH, "ab") as stderr_fid:
                stderr_fid.write(stderr)
            self.scanner_proc = None

    def get_scanner_logs(self):
        """Returns the stdout, stderr log files (returns empty strings if not found)"""
        output_log = ""
        error_log = ""
        if os.path.exists(GocatorModel.STDOUTPATH):
            with open(GocatorModel.STDOUTPATH, "rb") as stdout_fid:
                output_log = stdout_fid.read()
            with open(GocatorModel.STDERRPATH, "rb") as stderr_fid:
                error_log = stderr_fid.read()
        return output_log, error_log

    def profile(self, data_file, img_file):
        """Produces a basic plot of the specified data file, saved as PNG to specified image file."""
        matplotlib.rcParams['axes.formatter.limits'] = -4, 4
        matplotlib.rcParams['font.size'] = 9
        matplotlib.rcParams['axes.titlesize'] = 9
        matplotlib.rcParams['axes.labelsize'] = 9
        matplotlib.rcParams['xtick.labelsize'] = 8
        matplotlib.rcParams['ytick.labelsize'] = 8
        figure = Figure()
        canvas = FigureCanvas(figure)
        axes = figure.gca()
        x,y,z = np.genfromtxt(data_file, delimiter=",", unpack=True)
        # TODO - uncomment following when scanner connected (filters bad Z readings from scanner)
        #xi = x[z!=-32.768]
        #yi = y[z!=-32.768]
        #zi = z[z!=-32.768]
        xi=x
        yi=y
        zi=z
        scatter_plt = axes.scatter(xi, yi, c=zi, cmap=cm.get_cmap("Set1"))
        axes.grid(True)
        axes.axis([np.min(xi), np.max(xi), np.min(yi), np.max(yi)])
        figure.colorbar(scatter_plt)
        figure.savefig(img_file)