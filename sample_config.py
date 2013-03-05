"""sample_config.py - contains an example of a Gocator UI configuration.
Create a similar file config.py to configure each Gocator UI installation.

Chris R. Coughlin (TRI/Austin, Inc.)
"""

import os

DEBUG = False
BASEPATH = os.path.dirname(os.path.abspath(__file__))
# Output path for generated plots
OUTPUTIMAGEPATH = os.path.join(BASEPATH, 'static', 'data', 'img')
# Output path for profile data
OUTPUTDATAPATH = os.path.join(BASEPATH, 'static', 'data')
SECRET_KEY = 'secret_key'
THREADS_PER_PAGE = 2
USERNAME = 'admin'
PASSWORD = 'admin'