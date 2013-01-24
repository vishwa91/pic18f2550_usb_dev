#!/bin/bash

# Module to test the LibUSB device

import usb.core

dev = usb.core.find(idVendor=0x04d8)
dev.set_configuration()
dev.write(1, 't')
