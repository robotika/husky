#!/usr/bin/python
"""
  Contest code for "Robotem Rovne (RR)" (Robot go Straight!)
  - taken from original example of Clearpath Robotics
"""

from clearpath.horizon import Horizon 
from clearpath.horizon.transports import Serial

import time

horizon = Horizon(transport=Serial, transport_args={'port':'/dev/ttyUSB1'})
#horizon = Horizon()
horizon.open()

def status_handler(code, payload, timestamp):
  print(payload.print_format())

#horizon.add_handler(status_handler, request = 'system_status')
#horizon.request_system_status(subscription = 1)

for i in range(1, 3):
  left_percent = right_percent = i * 10
  horizon.set_differential_output(left_percent, right_percent)
  time.sleep(0.5)

while True:
  horizon.set_differential_output(30, 33)
  time.sleep(0.5)

time.sleep(1)
horizon.close()

