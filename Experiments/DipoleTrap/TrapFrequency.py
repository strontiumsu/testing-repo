# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 17:36:29 2023

@author: E.Porter
"""

from scan_framework import Scan1D, TimeScan
from artiq.experiment import *
import numpy as np



from CoolingClass import _Cooling
from CameraClass import _Camera
# from repository.models.scan_models import DipoleTemperatureModel

class DipoleTrapFrequency_exp(Scan1D, TimeScan, EnvExperiment):

    def build(self, **kwargs):
        # required initializations

        super().build(**kwargs)

        self.enable_pausing = True
        self.enable_auto_tracking = False
        self.enable_profiling = False

        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)

        # scan settings
        self.scan_arguments(times = {'start':0.1*1e-3,
            'stop':20*1e-3,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':1*us,
            'ndecimals':2},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default':"Fit and Save"}
            )

        # attrs for this exp
        # self.setattr_argument('ScanType', EnumerationValue(['CoM', 'Tx', 'Tz']) )

        self.setattr_argument("load_time", NumberValue(15*1e-3,min=1.0*1e-3,max=5000.00*1e-3,scale=1e-3,
                     unit="ms"),"parameters")
        self.setattr_argument("Dipole_Power_On",NumberValue(0.5,min=0.0,max=5.0,scale=1),"parameters")
        self.setattr_argument("Dipole_Power_Off",NumberValue(0.01,min=0.0,max=5.0,scale=1, ndecimals = 4),"parameters")
        self.setattr_argument("off_time", NumberValue(2*1e-3,min=1.0*1e-3,max=10.00*1e-3,scale=1e-3,
                             unit="ms"),"parameters")


    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms(30)
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model = None
        self.register_model(self.model, measurement=False, fit=False)






    @kernel
    def before_scan(self):
        # runs before experiment take place

        #initialize devices on host
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off

        delay(10*ms)

        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()
        self.MOTs.dipole_power(self.Dipole_Power_On)



    @kernel
    def measure(self, point):
        t_delay = point
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)

        self.MOTs.dipole_power(self.Dipole_Power_On) # make sure dipole power is on
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(10*ms)
        self.MOTs.rMOT_pulse() # generate MOT

        delay(self.load_time) # load for fixed time
        self.MOTs.dipole_power(self.Dipole_Power_Off) # turn off (low power) trap
        delay(self.off_time)
        self.MOTs.dipole_power(self.Dipole_Power_On)
        delay(t_delay) # oscillate time
        self.MOTs.take_MOT_image(self.Camera) # image after variable drop time

        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.dipole_power(self.Dipole_Power_On)

        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        return 0  # return nothing for now, deal with in post
