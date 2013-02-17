#!/bin/python

"""
This file creates the window for displaying the output of the venous flow
detected by the analog and digital modules. The input is from a PIC18F2550
libUSB device. Since the maximum frequency of sampling we need is around
10 Hertz, the low sampling rate of the USB device will not pose a problem.

This module is derived from the dynamic matplotlib wxpython by Eli Bendersky
and is based on wxpython and matplotlib.

Author:     Vishwanath
License:    Not applicable yet

"""
