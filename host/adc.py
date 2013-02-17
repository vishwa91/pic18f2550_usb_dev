#!/bin/bash

from scipy import *
from matplotlib.pyplot import *
import usb.core

dev = usb.core.find(idVendor=0x04d8)
dev.set_configuration()

# wait till the user gives a signal for starting measurement.
while(raw_input("Start") not in 'yy'):
      pass
# start measurement.
axis1 = []
axis2 = []

while(1):
    try:
        dev.write(1, 'A0')
        digit1, digit2 = dev.read(0x81, 64)[:2]
        axis1.append( digit1 + 256*digit2 )
        dev.write(1, 'A1')
        digit1, digit2 = dev.read(0x81, 64)[:2]
        axis2.append( digit1 + 256*digit2 )
    except KeyboardInterrupt:
        print "Done sampling."
        break
clf()
lenmin = min(len(axis1), len(axis2))
axis1 = axis1[:lenmin]
axis2 = axis2[:lenmin]
plot(axis1, axis2, 'b')
show()
