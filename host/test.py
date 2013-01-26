#!/bin/bash

# Module to test the LibUSB device

import usb.core
from time import sleep

dev = usb.core.find(idVendor=0x04d8)
dev.set_configuration()

while(1):
    dev.write(1, 't')
    sleep(0.5)
