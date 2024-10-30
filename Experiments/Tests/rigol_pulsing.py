# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 14:24:08 2024

@author: ejporter
"""

from scan_framework import Scan1D, TimeFreqScan
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import *

# imports
import numpy as np
import pyvisa
from time import sleep
from repository.models.scan_models import RabiModel


class rigol_pulsing_exp(Scan1D, TimeFreqScan, EnvExperiment):


    def build(self, **kwargs):

        super().build(**kwargs)
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("ttl1")

        self.rigol= None

        # self.setattr_argument("vel_sel_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
        #        unit="us"),"parameters")
        # self.setattr_argument("vel_sel_amp", NumberValue(0.5,min=0.0,max=1.0,scale=1,
        #        unit="V"),"parameters")

        # self.setattr_argument("rabi_amp", NumberValue(0.5,min=0.0,max=1.0,scale=1,
        #        unit="V"),"parameters")

        # self.setattr_argument("rabi_delay", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
        #        unit="us"),"parameters")

        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times = {'start':0*us,
            'stop':20*us,
            'npoints':20,
            'unit':"us",
            'scale':us,
            'global_step':0.1*us,
            'ndecimals':2},
             frequencies={
            'start':-1000*kHz,
            'stop':1000*kHz,
            'npoints':50,
            'unit':"kHz",
            'scale':kHz,
            'global_step':0.1*kHz,
            'ndecimals':3},
            frequency_center={'default':100.043*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}

            )



    def prepare(self):
        # self.prepare_rigol()

         # register model with scan framework
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=True)


    @kernel
    def before_scan(self):
        self.core.reset()


        delay(100*ms)
        self.ttl1.output()
        delay(1*ms)
        self.core.wait_until_mu(now_mu())



    def after_scan(self):
        self.rigol.write(":OUTP1 OFF");

    @kernel
    def measure(self, time, frequency):

        pulse_time = time
        freq = frequency


        self.core.reset()

        delay(1*ms)

        self.ttl1.pulse(10*us)

        delay(500*ms)
        self.core.wait_until_mu(now_mu())

        return 0




    # def before_measure(self, point, measurement):

    #     pulse_length = 50*us
        # ramp_up_time = 10*us
        # s = 6/ramp_up_time
        # mu = pulse_length/2
        # sigma = mu/3.5
        # amp_pedastal = 0.1
        # amp_gauss = 0.5

        # SAMPLES = 6000
        # t = np.linspace(0, pulse_length, SAMPLES)
        # y = 0.5*(1+np.tanh(s*(t-3/s))*np.tanh(s*(pulse_length-t-3/s)))
        # y_gauss = np.exp(-(t - mu)**2/2/sigma**2)


        # val_str = ",".join(map(str, y))
        # val_str_gauss = ",".join(map(str, y_gauss))

        # self.rigol.write(":OUTP1 OFF");
        # self.rigol.write(":OUTP2 OFF");



        # self.rigol.write("SOUR2:TRACE:DATA VOLATILE," + val_str)
        # self.rigol.write("SOUR1:TRACE:DATA VOLATILE," + val_str_gauss)
        # self.rigol.write(f":SOUR2:APPL:USER {1/pulse_length}, {2*amp_pedastal}, 0, 0")
        # self.rigol.write(f":SOUR1:APPL:USER {1/pulse_length}, {2*amp_gauss}, 0, 0")

        # self.rigol.write("SOUR1:BURS ON")
        # self.rigol.write("SOUR1:BURS:MODE TRIG")
        # self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        # self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")


        # self.rigol.write(":OUTP1 ON");


        # self.rigol.write("SOUR2:BURS ON")
        # self.rigol.write("SOUR2:BURS:MODE TRIG")
        # self.rigol.write(":SOUR2:BURS:NCYC 1 ")
        # self.rigol.write(":SOUR2:BURS:TRIG:SOUR EXT")


        # self.rigol.write(":OUTP2 ON");


    def prepare_rigol(self):
        rm = pyvisa.ResourceManager()
        # self.rigol = rm.open_resource('USB0::0x1AB1::0x0641::DG4E232700930::INSTR')
        # try:
        #     assert "DG4062" in self.rigol.query("*IDN?")
        # except AssertionError:
        #     print("Thrown Error: No such device")
        #     pass

        # self.rigol.write(":OUTP2 OFF");
        # self.rigol.write(":OUTP1 OFF");
