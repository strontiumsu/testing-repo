# # -*- coding: utf-8 -*-
# """
# Created on Wed Mar 15 16:01:28 2023

# @author: E. Porter
# """

from scan_framework import Scan1D
from artiq.experiment import *
import numpy as np
import time

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from CoolingClass import _Cooling
from ThreePhotonClass import _ThreePhoton
from PicomotorClass import _Picomotor
from CameraClass import _Camera
from repository.models.scan_models import PicoModel


class Picomotor_scan(Scan1D, EnvExperiment):
    
    
    def build(self, **kwargs):

        super().build(**kwargs)
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.ThPh = _ThreePhoton(self)
        self.Pico = _Picomotor(self)
        
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks


        self.setattr_argument('steps', Scannable(
            default=RangeScan(
                start=-2500,
                stop=2500,
                npoints=20
            ),
            scale=1,
            ndecimals=0,
            global_step=1
        ), group='Scan Range')
        self.setattr_argument("Time",NumberValue(0*1e-6,min=0.0*1e-6,max=100.00*1e-6,scale = 1e-6,
                      unit="us"),"Params")
        self.setattr_argument('Motor', EnumerationValue(['1', '2']), "Params")
        self.setattr_argument('ScanBeam', EnumerationValue(['1', '2', '3']), "Params")
        self.setattr_argument('Shelf', BooleanValue(True), "Detection")
        
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"No Fits"})
        self.t0 = np.int64(0)
        self.ind = 1
    def get_scan_points(self):
        return self.steps

    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.ThPh.prepare_aoms()
        self.Camera.camera_init()
        # register model with scan framework
        self.enable_histograms = True

        self.model = PicoModel(self)
        self.register_model(self.model, measurement=True, fit=True)
        self.Pico.set_home(int(self.Motor))
       
        
    @kernel
    def before_scan(self):
        # runs before experiment take place
        
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)  # initializes whiling keeping them off
        
        delay(10*ms)
        
        self.MOTs.take_background_image_exp(self.Camera)
        self.MOTs.AOMs_on(['3D', '2D', 'Zeeman', "3P0_repump", "3P2_repump"])
        delay(5000*ms)
        self.MOTs.AOMs_off(['3D', '2D', 'Zeeman', "3P0_repump", "3P2_repump"])
        
    
    def after_scan(self):
        self.Pico.set_position(int(self.Motor), 0)
    
        
    def before_measure(self, point, measurement):
        self.Pico.set_position(int(self.Motor), int(point))
    
    @kernel    
    def measure(self, point):
        pulse_time = self.Time
        #prepare
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(500*ms)
        self.Camera.arm()
        delay(200*ms)
        self.t0 = now_mu()
        
        
        # set freqs/phases
        self.ThPh.set_AOM_phase('Beam1', self.ThPh.freq_Beam1 , 0.0, self.t0, 0)            
        self.ThPh.set_AOM_phase('Beam2', self.ThPh.freq_Beam2 , 0.0, self.t0, 0)
        self.ThPh.set_AOM_phase('Beam3', self.ThPh.freq_Beam3 , 0.0, self.t0, 0)
       
        # perform experiment
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(5*ms)
        self.MOTs.rMOT_pulse()  # generates the red MOT        
        self.ThPh.set_field()        
        self.ThPh.threePhoton_pulse(pulse_time)
        
    
        # image
        if self.Shelf:
            self.MOTs.shelf()
        self.MOTs.push()
        self.MOTs.take_MOT_image(self.Camera)
        
        
    
        #process and output
        self.MOTs.AOMs_on(self.MOTs.AOMs) # just keeps AOMs warm
        delay(50*ms)
        self.Camera.process_image(save=True, name=self.ind, bg_sub=True)
        self.ind += 1
        delay(400*ms)        
        return self.Camera.get_push_stats()


