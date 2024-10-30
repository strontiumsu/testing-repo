# -*- coding: utf-8 -*-
"""
Created on Wed Sep 25 14:42:18 2024

@author: ejporter
"""

from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np


import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from repository.models.scan_models import BlankModel

class cavity_stability_exp(Scan1D, TimeScan, EnvExperiment):

    def build(self, **kwargs):
        # required initializations

        super().build(**kwargs)

        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False
        self.setattr_device("ttl2")

        # scan settings
        self.scan_arguments(times = {'start':0.1*1e-3,
            'stop':50*1e-3,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':1*us,
            'ndecimals':2},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default':"No Fits"}
            )

        self.setattr_argument("scan_duration", NumberValue(1000*1e-6,min=1.0*1e-6,max=10000.00*1e-6,scale = 1e-6,
                      unit="us"),"Parameters")
        self.setattr_argument("delay_duration", NumberValue(10*1e-6,min=1.0*1e-6,max=100000.00*1e-6,scale = 1e-6,
                      unit="us"),"Parameters")


    def prepare(self):

        # register model with scan framework
        self.enable_histograms = True
        self.model = BlankModel(self)
        self.register_model(self.model, measurement=True, fit=True)


    @kernel
    def before_scan(self):
        self.core.reset()
        delay(1*ms)
        self.ttl2.output()



    @kernel
    def measure(self, point):
        time_delay = point
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(1*ms)

        for _ in range(3):
            self.ttl2.pulse(self.scan_duration)
            delay(self.delay_duration)
        delay(time_delay)





        return 0
