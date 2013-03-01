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
Name:       VenoScope(VS)

"""

import time
import usb.core
import wx
from scipy import *

# Matplotlib imports
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import pylab

def _configure_device():
    """ Configure and get the USB device running. Returns device class if
    success and None if failed"""
    vendor_id = 0x04D8          # These ids are microchip's libusb based device
    product_id = 0x0204         # ids
    dev = usb.core.find(idVendor=vendor_id, idProduct = product_id)
    try:
        dev.set_configuration()
        return dev
    except:
        return None

class VSDataAquisition(object):
    """ A place holder for collecting data from the ADC of the device. This
    class will also control sample/hold bit of the device."""
    def __init__(self):
        """ Configure the device and set class properties"""
        self.data0 = []     # This will hold data from ADC0
        self.data1 = []     # This will hold data from ADC1
        self.dev = _configure_device()

    def get_data(self):
        """ Get the next data from ADC0. For ADC1, use get_dc_offset()"""
        self.dev.write(1, 'A0')
        digit1, digit2 = self.dev.read(0x81, 64)[:2]
        # Save the data as voltage between 0.0 and 5.0
        self.data0.append((digit1 + 256*digit2)*5.0/1024)
        
    def get_dc_offset(self):
        """ Get the initial DC offset of the analog output"""
        self.dev.write(1, 'A1')
        digit1, digit2 = self.dev.read(0x81, 64)[:2]
        # Save the data as voltage between 0.0 and 5.0
        self.data1.append((digit1 + 256*digit2)*5.0/1024)

    def sample(self):
        """ Set the sample bit for getting intial DC offset"""
        self.dev.write(1, 'S')

    def hold(self):
        """ Clear the sample bit for consecutive data aquisition"""
        self.dev.write(1, 'H')

class VSControlBox(wx.Panel):
    """ A static box for controlling the start and stop of the device and
    displaying the final result of the venous flow measurement."""
    def __init__(self, parent, ID, label):
        wx.Panel.__init__(self, parent, ID)
        
        # Create two box sizers, one for the button and one for the status
        # message and final output reading.
        button_box = wx.StaticBox(self, -1, label = 'Device Control')
        info_box = wx.StaticBox(self, -1, label = 'Information')
        box = wx.StaticBox(self, -1, label)
        main_sizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        button_sizer = wx.StaticBoxSizer(button_box, orient=wx.HORIZONTAL)
        info_sizer = wx.StaticBoxSizer(info_box, orient=wx.HORIZONTAL)
        
        # Create a start/stop measurement button.
        self.start_button = wx.Button(self, label = 'Start measurement',)
        # Create a result and information text box.
        self.result_box = wx.StaticText(self)
        self.txt_info_box = wx.StaticText(self, size=(200, -1))
        self.result_box.SetLabel("0.00")
        
        # Add the items to sizers
        button_sizer.Add(self.start_button, 0, wx.ALL, 10)
        info_sizer.Add(self.result_box, 0, wx.ALL, 10)
        info_sizer.Add(self.txt_info_box, 0, wx.ALL, 10)

        # Add the sizers to main sizer
        main_sizer.Add(button_sizer, flag=wx.ALIGN_CENTER_VERTICAL)
        main_sizer.AddSpacer(20)
        main_sizer.Add(info_sizer, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

        # Bind events to the button
        self.start_button.Bind(wx.EVT_BUTTON, parent.Parent.start_stop)

        # Finally, make a fit
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        
    def start_stop(self, event):
        """ Bind a rudimentary event now. Will update it later."""
        self.start_button.SetLabel('Measuring')
        self.start_button.Enable = False
        # Do nothing as of now. Will call measuring functions later.
        self.txt_info_box.SetLabel('Starting measurement.')
        time.sleep(2)
        self.start_button.SetLabel('Start measurement')
        self.start_button.Enable = True
        self.txt_info_box.SetLabel('Completed measurement.')
        self.result_box.SetLabel("100.00")
        

class VSGraphFrame(wx.Frame):
    """ Main frame for the measurement application"""
    title = "Venous flow calculation"
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)
        self.SAMPLING_TIME = 10000.0    # Set the sampling time here.
        
        self.daq = VSDataAquisition()
        if self.daq == None:
            help_string = ''' Device is not connected. Please connect the
device and restart the software'''
            wx.MessageBox(help_string, 'Device not found', 
                  wx.OK | wx.ICON_INFORMATION)
            self.Destroy()
            return
        self.create_menu()          # Create the menu
        self.create_status_bar ()   # Add a status bar. Could use for debugging
        self.create_main_panel()    # The main panel
        
        # We will use a timer for getting our samples.
        self.redraw_timer = wx.Timer(self, wx.ID_ANY)
        # Sampling duration itself is another timer. This timer is a
        # oneshot timer and runs for SAMPLING_TIME time.
        self.sampling_timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.Bind(wx.EVT_TIMER, self.on_sampling_timer, self.sampling_timer)
        self.redraw_timer.Start(100)

    def create_menu(self):
        """ Add menu bar items. One File and one About"""
        self.menubar = wx.MenuBar()
        menu_file = wx.Menu()
        menu_help = wx.Menu()
        # Add save and exit to File menu
        menu_save = menu_file.Append(-1, '&Save plot\tCtrl-S',
                                     'Save plot to a file')
        menu_file.AppendSeparator()
        menu_exit = menu_file.Append(-1, '&Exit\tCtrl-X',
                                     'Exit the program')
        self.Bind(wx.EVT_MENU, self.on_save, menu_save)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)
        # Add an about in the Help menu. Will update later.
        help_about = menu_help.Append(-1, '&About',
                                      'About the program')
        menu_help.AppendSeparator()
        self.Bind(wx.EVT_MENU, self.on_about, help_about)

        # Add them both to menubar
        self.menubar.Append(menu_file, '&File')
        self.menubar.Append(menu_help, '&Help')
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        """ Create the main panel which will show the dynamic plot."""
        self.panel = wx.Panel(self)

        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)

        self.control_box = VSControlBox(self.panel, -1, 'Information board')

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.control_box, 0, wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)
        
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def create_status_bar(self):
        """ Create a status bar. Will use it in future for debugging"""
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):
        """ Initialize the plot canvas"""
        self.dpi = 100
        self.fig = Figure((5.0, 5.0), dpi = self.dpi)

        self.main_plot = self.fig.add_subplot(111)
        self.main_plot.set_axis_bgcolor('black')
        self.main_plot.set_title('Dynamic venous flow view', size = 12)

        pylab.setp(self.main_plot.get_xticklabels(), fontsize = 8)
        pylab.setp(self.main_plot.get_yticklabels(), fontsize = 8)

        # Plot the data as a green line
        self.plot_data = self.main_plot.plot(
            self.daq.data0,
            linewidth = 1,
            color = (0, 1, 0),
            )[0]
        self.main_plot.grid(True, color='gray')

    def draw_plot(self):
        """ Redraw the plot after every data aquisition."""
        # X axis is auto follow.
        XLEN = 100
        xmax = max(len(self.daq.data0), XLEN)
        xmin = xmax - XLEN

        # The Y value will lie between 0.0 and 5.0 volts
        ymax = 5.0
        ymin = 0.0

        self.main_plot.set_xbound(lower=xmin, upper=xmax)
        self.main_plot.set_ybound(lower=ymin, upper=ymax)

        # Add the grid. Grid looks cool and is actually very helpful.
        self.main_plot.grid(True, color='gray')

        pylab.setp(self.main_plot.get_xticklabels(), 
            visible=True)
        
        self.plot_data.set_xdata(arange(len(self.daq.data0)))
        self.plot_data.set_ydata(array(self.daq.data0))
        
        self.canvas.draw()

    def on_save(self, event):
        """ Method for saving a plot """
        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)

    def start_stop(self, event):
        """ Restart measurements and complete calculations"""
        self.daq.data0= []
        self.control_box.txt_info_box.SetLabel('Starting measurement')
        self.sampling_timer.Start(self.SAMPLING_TIME, oneShot=True)
            
    def on_redraw_timer(self, event):
        """ Update the plot whenever data is obtained """
        
        if self.sampling_timer.IsRunning():
            self.daq.get_data()
            self.draw_plot()
        else:
            self.control_box.txt_info_box.SetLabel('Measurement complete')
            self.calculate()
            return

    def on_sampling_timer(self, event):
        """ Stop the timer when sampling is complete."""
        self.sampling_timer.Stop()

    def calculate(self):
        """Calculate the venous flow rate. Dummy now."""
        if self.sampling_timer.IsRunning():
            return
        if self.daq.data0 == []:
            average = 0.0
        else:
            average = mean(self.daq.data0)
        res_string = '%.2f' %average
        self.control_box.result_box.SetLabel(res_string)

    def on_exit(self, event):
        """ Quit the window """
        self.Destroy
        
    def on_about(self, event):
        """ Display an about message """
        pass

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.frame = VSGraphFrame()
    app.frame.Show()
    app.MainLoop()
    
