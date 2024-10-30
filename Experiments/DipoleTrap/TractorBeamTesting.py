# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 14:01:03 2023

@author: E. Porter
"""

from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np


from CoolingClass import _Cooling
from CameraClass import _Camera
from repository.models.scan_models import TemperatureModel

class TractorBeamTesting(Scan1D, TimeScan, EnvExperiment):

    def build(self, **kwargs):
        # required initializations
        super().build(**kwargs)

        self.setattr_device("ttl7")

        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False

        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)

        # scan settings
        self.scan_arguments(times = {'start':0.1*1e-3,
            'stop':5*1e-3,
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



        self.setattr_argument("dipole_load_time",NumberValue(10*1e-3,min=0.0,max=100*1e-3,scale = 1e-3,
              unit="ms"),"Params")
    def prepare(self):

        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = TemperatureModel(self)
        self.register_model(self.model, measurement=True, fit=True)

    @kernel
    def before_scan(self):
        # runs before experiment take place
        self.core.reset()
        self.ttl7.output()
        self.ttl7.off()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off

        delay(10*ms)

        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(5000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()

    @kernel
    def measure(self, point):
        t = point
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)


        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(10*ms)
        self.MOTs.rMOT_pulse()
        delay(self.dipole_load_time)

        self.ttl7.on()  # triggers FM modulation
        delay(t)

        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        delay(50*ms)
        self.Camera.process_image(bg_sub=True)

        delay(400*ms)
        self.ttl7.off()
        delay(50*ms)

        return 0
