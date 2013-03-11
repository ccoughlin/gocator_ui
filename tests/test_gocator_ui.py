"""test_gocator_ui.py - tests the gocator_ui module

Chris R. Coughlin (TRI/Austin, Inc.)
"""

import json
import os
import sys
import gocator_ui
from models import gocator_model
from models.configobj import ConfigObj
import flask
import unittest

class TestGocatorUI(unittest.TestCase):
    """Tests the Gocator UI"""

    @classmethod
    def setUpClass(cls):
        """Stores current system configuration for restoration"""
        cls._original_cfg = ConfigObj(gocator_model.GocatorModel.ENCODERCONFIGPATH)

    @classmethod
    def tearDownClass(cls):
        """Restores system's original configuration"""
        cls._original_cfg.write()

    def setUp(self):
        gocator_ui.app.config['TESTING'] = True
        self.app = gocator_ui.app.test_client()
        self.gocator_model = gocator_model.GocatorModel()

    def tearDown(self):
        self.logout()

    def remove_file(self, file_name):
        """Helper function to delete file_name--swallows the WindowsError exception 
        Windows throws if file is in use."""
        if os.path.exists(file_name):
            if sys.platform.startswith('win32'):
                try:
                    os.remove(file_name)
                except WindowsError: 
                    pass
            os.remove(file_name)

    def test_temp_fnames(self):
        """Verify returning temporary filenames"""
        fldr = os.path.join(os.path.dirname(__file__), "support_files")
        temp_file = gocator_ui.temp_fname(fldr, ".txt")
        self.assertEqual(os.path.dirname(temp_file), fldr)
        self.assertTrue(temp_file.endswith('.txt'))
        self.remove_file(temp_file)

    def test_list_output(self):
        """Verify returning a list of stored data and plot files"""
        data_folder = gocator_ui.app.config['OUTPUTDATAPATH']
        plot_folder = os.path.join(data_folder, "img")
        expected_data_files = [fname for fname in os.listdir(data_folder) if fname.endswith("csv")]
        expected_plot_files = [fname for fname in os.listdir(plot_folder) if fname.endswith("png")]
        self.assertListEqual(expected_data_files, gocator_ui.list_data_files())
        self.assertListEqual(expected_plot_files, gocator_ui.list_plot_files())

    def login(self, username, password):
        """Helper function to log in to the admin sections of the site"""
        return self.app.post('/login', data=dict(user=username,
                                                 pword=password),
                             follow_redirects=True)

    def admin_login(self):
        """Helper function to log in as admin"""
        return self.login(gocator_ui.app.config['USERNAME'], gocator_ui.app.config['PASSWORD'])

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_good_login_logout(self):
        """Verify logging in and out of site"""
        rv = self.admin_login()
        self.assertTrue("Login successful" in rv.data)
        rv = self.logout()
        self.assertTrue("Logout successful" in rv.data)

    def test_bad_login_logout(self):
        """Verify rejecting bad logins"""
        rv = self.login(gocator_ui.app.config['USERNAME'], "")
        self.assertTrue("Invalid login" in rv.data)
        rv = self.login("", gocator_ui.app.config['PASSWORD'])
        self.assertTrue("Invalid login" in rv.data)

    def test_trigger_form(self):
        """Verify the configure trigger form works"""
        rv = self.app.get('/trigger', follow_redirects=True)
        self.assertTrue("Login required" in rv.data)
        self.admin_login()
        rv = self.app.get('/trigger', follow_redirects=True)
        self.assertTrue("Configure Triggering" in rv.data)

    def test_encoder_form(self):
        """Verify the configure encoder form works"""
        rv = self.app.get('/encoder', follow_redirects=True)
        self.assertTrue("Login required" in rv.data)
        self.admin_login()
        rv = self.app.get('/encoder', follow_redirects=True)
        self.assertTrue("Configure Encoder" in rv.data)

    def test_trigger_config(self):
        """Verify reading/writing the trigger configuration"""
        self.admin_login()
        rv = self.app.get('/trigger_config')
        trig_dict = json.loads(rv.data)
        self.assertDictEqual(self.gocator_model.get_configured_trigger(), trig_dict)
        trig_dict = self.gocator_model.get_sane_trigger()
        form_data = json.dumps({'triggertype':trig_dict['type'], 
                                'travel_threshold':trig_dict['travel_threshold'],
                                'travel_direction':trig_dict['travel_direction'],
                                'frame_rate':trig_dict['frame_rate'],
                                'use_gate':trig_dict['enable_gate']
                    })
        rv = self.app.post('/trigger_config', data=form_data, content_type="application/json")
        rv = self.app.get(rv.data)
        self.assertTrue("Configuration successful" in rv.data)

    def test_encoder_config(self):
        """Verify reading/writing the encoder configuration"""
        self.admin_login()
        rv = self.app.get('/encoder_config')
        encoder_dict = json.loads(rv.data)
        self.assertDictEqual(self.gocator_model.get_configured_encoder(), encoder_dict)
        encoder_dict = json.dumps(self.gocator_model.get_sane_encoder())
        rv = self.app.post('/encoder_config', data=encoder_dict, content_type="application/json")
        rv = self.app.get(rv.data)
        self.assertTrue("Configuration successful" in rv.data)

    def test_logs(self):
        """Verify returning/clearing the application logs"""
        rv = self.app.get('/logs')
        self.assertTrue("System Logs" in rv.data)
        rv = self.app.get('/clearlogs', follow_redirects=True)
        self.assertTrue("Login required" in rv.data)
        self.admin_login()
        rv = self.app.get('/clearlogs', follow_redirects=True)
        self.assertTrue("Logs cleared" in rv.data)

    def test_get_info(self):
        """Verify returning static information pages"""
        rv = self.app.get('/help')
        self.assertTrue("Help" in rv.data)
        rv = self.app.get('/tri')
        self.assertTrue("http://www.tri-austin.com" in rv.data)

    def test_scan(self):
        """Verify starting and stopping the scanner"""
        # Should return an error message - no data to plot
        rv = self.app.post("/scan", data=dict(get_plot="true", get_data="true"))
        response_dict = json.loads(rv.data)
        self.assertTrue(response_dict['scanning'])
        rv = self.app.post("/stopscan")
        response_dict = json.loads(rv.data)
        self.assertFalse(response_dict['scanning'])
        self.assertTrue(response_dict.has_key('error'))
        # Should be clean
        rv = self.app.post("/scan", data=dict(get_plot="false", get_data="true"))
        response_dict = json.loads(rv.data)
        self.assertTrue(response_dict['scanning'])
        rv = self.app.post("/stopscan")
        response_dict = json.loads(rv.data)
        self.assertFalse(response_dict['scanning'])
        self.assertFalse(response_dict.has_key('error'))
        self.assertTrue(response_dict.has_key('image'))
        self.assertTrue(response_dict.has_key('data'))

    def test_target(self):
        """Verify starting and stopping the scanner in targeting mode"""
        rv = self.app.post("/target")
        response_dict = json.loads(rv.data)
        self.assertTrue(response_dict['running'])
        rv = self.app.post("/stoptarget")
        response_dict = json.loads(rv.data)
        self.assertFalse(response_dict['running'])

    def test_data(self):
        """Verify returning a list of stored data and clearing it"""
        rv = self.app.get("/data")
        self.assertTrue("Data" in rv.data)
        data_files = os.listdir(gocator_ui.app.config['OUTPUTDATAPATH'])
        for data_file in data_files:
            if data_file.endswith("csv"):
                self.assertTrue(os.path.basename(data_file) in rv.data)
        rv = self.app.get('/cleardata', follow_redirects=True)
        self.assertTrue("Login required" in rv.data)
        self.admin_login()
        rv = self.app.get('/cleardata', follow_redirects=True)
        self.assertTrue("Data Erased" in rv.data)
        self.assertEqual(len(gocator_ui.list_data_files()), 0)
        self.assertEqual(len(gocator_ui.list_plot_files()), 0)

if __name__ == "__main__":
    unittest.main()