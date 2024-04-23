# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 12:25:08 2022

@author: sr
"""

from scan_framework import Scan2D
from artiq.experiment import *
import numpy as np
import time

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from CameraClass import _Camera

from repository.models.scan_models import RamseyPhaseModel
from repository.models.scan_models import RamseyDecayModel


class BlueMOT_Atom_Number(Scan2D, EnvExperiment): # note python works from left to right with inheritances
    
    def build(self, **kwargs):
        # required attrs, calls the core + scheduler

        super().build(**kwargs)
        self.setattr_device("core")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks
            
        self.t0 = np.int64(0)
        self.ind = 1
        self.ramsey_phase_exp = 0.0*1e-6
        self.delay_exp = 0.0*1e-6
        
        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        
        self.setattr_argument("Rabi_t_pi",
                              NumberValue(0.25*1e-6,min=0.0,max=20.00*1e-6,scale = 1e-6,
                                unit="us"),"Ramsey")
        
        
        self.setattr_argument('ramsey_phase', Scannable(
            default=RangeScan(
                start=0.0,
                stop=2.0,
                npoints=20
            ),
            scale=1,
            ndecimals=2,
            global_step=0.1, 
            unit="Turns"
        ), group='Ramsey')
        
        self.setattr_argument('delay', Scannable(
            default=RangeScan(
                start=0.0,
                stop=20.0e-6,
                npoints=20
            ),
            scale=1e-6,
            ndecimals=2,
            unit="us"
        ), group='Ramsey')
        
        # scan arguments
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})
        
        self.setattr_argument("heat_time",NumberValue(1*1e-6,min=0.0,max=100*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument("heat",BooleanValue(False),"Params")
        
        self.scan0 = 0
        self.scan1 = 0
    def get_scan_points(self):
        return [self.delay, self.ramsey_phase]
    
    @kernel
    def set_scan_point(self, i_point, point):
        self.ramsey_phase_exp = point[1]
        self.delay_exp = point[0]
        self.core.break_realtime()
        
        
    def prepare(self):
         #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True
        self.model1 = RamseyDecayModel(self)
        self.model2 = RamseyPhaseModel(self)
        self.register_model(self.model1, dimension=0, fit=True, set=True)
        self.register_model(self.model2, dimension=1, fit=True, set=True, measurement=True)
        
        
    @kernel
    def before_scan(self):
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        delay(1000*ms)   
        
        
    @kernel
    def measure(self, point):
        
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1, self.ramsey_phase_exp, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2, 0.0, self.t0, 1)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3, 0.0, self.t0, 1)
            # make this more compact 
        self.ThPh.switch_profile(0) 
        
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(5*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT 
        with parallel:
            if self.heat:
                self.MOTs.set_AOM_freqs([('3D', self.MOTs.f_MOT3D_detect)])
                self.MOTs.set_AOM_attens([('3D', 6.0)]) 
            self.ThPh.set_field()  
        if self.heat:
            with sequential:                   
                self.MOTs.AOMs_on(['3D'])
                delay(self.heat_time)
                self.MOTs.AOMs_off(['3D'])
        else:
            delay(self.heat_time)
        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        
        self.ThPh.switch_profile(1)
        delay(self.delay_exp)  # offset by half a micro second

        self.ThPh.threePhoton_pulse(self.Rabi_t_pi)
        
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        self.Camera.process_image(bg_sub=True)
        delay(100*ms) 
        self.ind += 1
        val = self.Camera.get_push_stats()
        self.write_val(val)
        return val
    
    def calculate_dim0(self, dim1_model):
        param = 2*dim1_model.fit.params.A
        # weight final fit by error in this dimension 1 fit param
        error = dim1_model.fit.errs.A_err
        self.set_dataset(f"ContrastMeasurement__{self.scan1}", param, broadcast=False)
        self.scan1 += 1
        return param, error
    
    def write_val(self, val):
        self.set_dataset(f"PhaseMeasurement_{self.scan0}_{self.scan1}", val, broadcast=False)
        self.scan0 += 1
    





    
    