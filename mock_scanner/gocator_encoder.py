"""gocator_encoder.py - mock Gocator control application used during UI testing

Chris R. Coughlin (TRI/Austin, Inc.)
"""

import time
import random
import sys

# Dummy text to populate stdout
lorem_text = ['Lorem ipsum dolor sit amet, consectetuer adipiscing elit',
              'Aenean commodo ligula eget dolor',
              'Aenean massa',
              'Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus',
              'Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem',
              'Nulla consequat massa quis enim', 'Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu',
              'In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo',
              'Nullam dictum felis eu pede mollis pretium',
              'Integer tincidunt',
              'Cras dapibus',
              'Vivamus elementum semper nisi',
              'Aenean vulputate eleifend tellus',
              'Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim',
              'Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus',
              'Phasellus viverra nulla ut metus varius laoreet',
              'Quisque rutrum',
              'Aenean imperdiet',
              'Etiam ultricies nisi vel augue',
              'Curabitur ullamcorper ultricies nisi',
              'Nam eget dui',
              'Etiam rhoncus',
              'Maecenas nec odio et ante tincidunt tempus',
              'Donec vitae sapien ut libero venenatis faucibus',
              'Nullam quis ante',
              'Etiam sit amet orci eget eros faucibus tincidunt',
              'Duis leo']


if __name__ == "__main__":
    random.seed()
    while True:
        user_input = raw_input()
        if 'q'in user_input:
            sys.stderr.write(("{0} -- {1}\n".format(time.strftime("%a%b%Y_%H%M"), random.choice(lorem_text))))
            sys.stderr.write("{0} -- {1}\n".format(time.strftime("%a%b%Y_%H%M"), "Operation halted by user"))
            break
        print("{0} -- {1}".format(time.strftime("%a%b%Y_%H%M"), random.choice(lorem_text)))
        time.sleep(1)