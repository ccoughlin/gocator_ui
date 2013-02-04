"""test_gocator_model.py - tests the gocator_model module

Chris R. Coughlin (TRI/Austin, Inc.)
"""

import unittest
import os.path
import random
from models import gocator_model
from models.configobj import ConfigObj

class TestGocatorModel(unittest.TestCase):
    """Tests the GocatorModel class"""

    SUPPORTFILESPATH = os.path.join(os.path.dirname(__file__), 'support_files')
    SAMPLECFGPATH = os.path.join(SUPPORTFILESPATH, 'sample_config.cfg')
    SAMPLEINPUTDATA = os.path.join(SUPPORTFILESPATH, 'sample_data.csv')
    OUTPUTPATH = os.path.join(SUPPORTFILESPATH, 'sample_output.csv')

    def setUp(self):
        self.model = gocator_model.GocatorModel(TestGocatorModel.SAMPLECFGPATH)
        self.cfg = ConfigObj(TestGocatorModel.SAMPLECFGPATH)

    @property
    def default_trigger(self):
        """Returns the default trigger settings"""
        return {'type':'Encoder',
                'enable_gate':False,
                'frame_rate':300,
                'travel_threshold':1,
                'trigger_direction':'bidirectional'}

    @property
    def configured_trigger(self):
        """Returns the configuration of the trigger"""
        trig = self.default_trigger
        if "Trigger" in self.cfg:
            trigger_config = self.cfg["Trigger"]
            if 'type' in trigger_config:
                acceptable_trigger_types = ['encoder', 'time', 'input']
                if trigger_config['type'].lower() in acceptable_trigger_types:
                    trig['type'] = trigger_config['type'].title()
            if 'enable_gate' in trigger_config:
                trig['enable_gate'] = trigger_config.as_bool('enable_gate')
            if 'frame_rate' in trigger_config:
                trig['frame_rate'] = trigger_config.as_int('frame_rate')
            if 'travel_threshold' in trigger_config:
                trig['travel_threshold'] = trigger_config.as_float('travel_threshold')
            if 'trigger_direction' in trigger_config:
                acceptable_directions = ['forward', 'backward', 'bidirectional']
                if trigger_config['trigger_direction'].lower() in acceptable_directions:
                    trig['trigger_direction'] = trigger_config['trigger_direction'].title()
        return trig

    @configured_trigger.setter
    def configured_trigger(self, new_trigger_config):
        """Saves the trigger config"""
        if 'Trigger' not in self.cfg:
            self.cfg['Trigger'] = {}
        trigger_config = self.cfg['Trigger']
        trigger_config['type'] = new_trigger_config['type'].title()
        trigger_config['enable_gate'] = new_trigger_config['enable_gate']
        if 'frame_rate' in new_trigger_config:
            trigger_config['frame_rate'] = new_trigger_config['frame_rate']
        if 'travel_threshold' in new_trigger_config:
            trigger_config['travel_threshold'] = new_trigger_config['travel_threshold']
        if 'trigger_direction' in new_trigger_config:
            trigger_config['trigger_direction'] = new_trigger_config['trigger_direction'].title()
        self.cfg.write()

    @property
    def default_encoder(self):
        """Returns the default encoder settings"""
        return {'encoder_model':'unspecified', 'encoder_resolution':0}

    @property
    def configured_encoder(self):
        """Returns the linear magnetic encoder configuration"""
        lme = self.default_encoder
        if 'Encoder' in self.cfg:
            encoder_config = self.cfg['Encoder']
            if 'resolution' in encoder_config:
                lme['encoder_resolution'] = encoder_config.as_float('resolution')
            if 'model' in encoder_config:
                lme['encoder_model'] = encoder_config['model']
        return lme

    @configured_encoder.setter
    def configured_encoder(self, new_encoder_config):
        """Saves the new encoder configuration"""
        if 'Encoder' not in self.cfg:
            self.cfg['Encoder'] = {}
        encoder_config = self.cfg['Encoder']
        if 'encoder_model' in new_encoder_config:
            encoder_config['model'] = new_encoder_config['encoder_model']
        if 'encoder_resolution' in new_encoder_config:
            encoder_config['resolution'] = new_encoder_config['encoder_resolution']
        self.cfg.write()

    def test_get_sane_trigger(self):
        """Verify returning sane defaults for trigger settings"""
        self.assertDictEqual(self.default_trigger, self.model.get_sane_trigger())

    def test_get_configured_trigger(self):
        """Verify returning trigger config"""
        self.assertDictEqual(self.configured_trigger, self.model.get_configured_trigger())

    def test_set_configured_trigger(self):
        """Verify setting trigger config"""
        original_trig = self.configured_trigger
        new_trig = self.default_trigger
        new_trig['frame_rate'] = random.randint(300, 5000)
        new_trig['travel_threshold'] = random.randint(0, 100)
        new_trig['trigger_direction'] = random.choice(['Forward', 'Backward', 'Bidirectional'])
        self.model.set_configured_trigger(new_trig)
        self.assertDictEqual(new_trig, self.model.get_configured_trigger())
        self.configured_trigger = original_trig

    def test_get_sane_encoder(self):
        """Verify returning sane defaults for encoder settings"""
        self.assertDictEqual(self.default_encoder, self.model.get_sane_encoder())

    def test_get_configured_encoder(self):
        """Verify returning encoder config"""
        self.assertDictEqual(self.configured_encoder, self.model.get_configured_encoder())

    def test_set_configured_encoder(self):
        """Verify setting encoder config"""
        original_lme = self.configured_encoder
        new_lme = self.default_encoder
        new_lme['encoder_model'] = random.choice(['Alpha', 'Beta', 'Gamma', 'Potato'])
        new_lme['encoder_resolution'] = random.randint(0, 100)
        self.model.set_configured_encoder(new_lme)
        self.assertDictEqual(new_lme, self.model.get_configured_encoder())
        self.configured_encoder = original_lme

    def start_scanner(self):
        """Attempts to start the scanner process, returns True if scanner process is running."""
        return self.model.start_scanner(TestGocatorModel.OUTPUTPATH)

    def test_start_scanner(self):
        """Verify starting the scanner process"""
        self.assertTrue(self.start_scanner())
        self.model.stop_scanner()

    def test_stop_scanning(self):
        """Verify stopping the scanner process"""
        self.model.stop_scanner()
        self.assertFalse(self.model.scanner_running)
        self.model.clear_scanner_logs()

    def test_profile(self):
        """Verify creating a scatter plot of data"""
        img_file = os.path.join(TestGocatorModel.SUPPORTFILESPATH, "test_profile.png")
        self.model.profile(TestGocatorModel.SAMPLEINPUTDATA, img_file)
        self.assertTrue(os.path.exists(img_file))
        try:
            os.remove(img_file)
        except WindowsError: # File in use
            pass

    def test_get_scanner_logs(self):
        """Verify returning standard output and standard error log files"""
        self.start_scanner()
        self.model.stop_scanner()
        standard_output, standard_error = self.model.get_scanner_logs()
        self.assertTrue(isinstance(standard_output, str))
        self.assertTrue(isinstance(standard_error, str))
        self.model.clear_scanner_logs()

    def test_clear_scanner_logs(self):
        """Verify deleting the scanner logs"""
        self.start_scanner()
        self.model.stop_scanner()
        self.model.clear_scanner_logs()
        standard_output, standard_error = self.model.get_scanner_logs()
        self.assertTrue(len(standard_output)==0)
        self.assertTrue(len(standard_error)==0)

if __name__  == "__main__":
    random.seed()
    unittest.main()
