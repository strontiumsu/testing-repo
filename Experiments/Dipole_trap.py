# -*- coding: utf-8 -*-
"""
Created on Fri May 26 11:18:52 2023

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 12:25:08 2022

@author: sr
"""

from scan_framework import Scan2D
import time
from artiq.experiment import *
import numpy as np
from scipy.optimize import curve_fit
from numpy import unravel_index

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera
from repository.models.scan_models import RamseyPhaseModel
from repository.models.scan_models import RamseyDecayModel


class Dipole_trap_exp(Scan2D, EnvExperiment): # note python works from left to right with inheritances
    
    def build(self, **kwargs):
        # required attrs, calls the core + scheduler

        super().build(**kwargs)
        self.setattr_device("core")
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
                
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        self.ind = 1
        self.V2_exp = 0.0
        self.V1_exp = 0.0

        self.setattr_argument('V2', Scannable(
            default=RangeScan(
                start=0.0,
                stop=4.0,
                npoints=20
            ),
            scale=1,
            ndecimals=2,
            global_step=0.1, 
            unit="V"
        ), group='DAC')
        
        self.setattr_argument('V1', Scannable(
            default=RangeScan(
                start=0.0,
                stop=4.0,
                npoints=20
            ),
            scale=1,
            ndecimals=2,
            unit="V"
        ), group='DAC')
        
        # scan arguments
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})
        
        self.setattr_argument("V3",NumberValue(0.0,min=0.0,max=4.00),"DAC")
        self.setattr_argument("delay_time",NumberValue(5*1e-3,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"Params")

        
        self.scan0 = 0
        self.scan1 = 0
    def get_scan_points(self):
        return [self.V1, self.V2]
    
    @kernel
    def set_scan_point(self, i_point, point):
        self.V2_exp = point[1]
        self.V1_exp = point[0]
        self.core.break_realtime()
        
        
    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms(N=80)
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model1 = RamseyPhaseModel(self)
        self.model2 = RamseyPhaseModel(self)
        self.register_model(self.model1, dimension=0, fit=False, set=True)
        self.register_model(self.model2, dimension=1, fit=False, set=True, measurement=True)
        
        
    @kernel
    def before_scan(self):
        self.core.reset()
        self.dac_0.init()
        delay(10*ms)
        
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump"])
        delay(1000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump"])
        self.MOTs.atom_source_off()
        
        
   
    @kernel
    def measure(self, point):
        
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        
        # Set DAC values
        self.dac_0.write_dac(5,self.V1_exp)
        self.dac_0.write_dac(6,self.V2_exp)
        self.dac_0.write_dac(7,self.V3)
        self.dac_0.load()
        
        
        
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(10*ms)
        self.MOTs.rMOT_pulse()
        
        #self.MOTs.rMOT_beam_pulse(self.delay_time)
        delay(self.delay_time)

        self.MOTs.take_MOT_image(self.Camera)
        delay(10*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        
        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        
        
        
        
        self.ind += 1
        val = int(self.V2_exp)
        self.write_val(val)
        return val
    
    def calculate_dim0(self, dim1_model):
        # param = 2*dim1_model.fit.params.A
        # weight final fit by error in this dimension 1 fit param
        # error = dim1_model.fit.errs.A_err
        #self.set_dataset(f"ContrastMeasurement__{self.scan1}", param, broadcast=False)
        self.scan1 += 1
        return 1, 0.1
    
    def write_val(self, val):
        self.set_dataset(f"PhaseMeasurement_{self.scan0}_{self.scan1}", val, broadcast=False)
        self.scan0 += 1
    





    
    
