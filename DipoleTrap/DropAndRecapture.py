# -*- coding: utf-8 -*-
"""
Created on Wed Oct 4 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, sequential, now_mu,BooleanValue

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg


class DropAndRecapture(EnvExperiment):


    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)


        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("image_wait_time", NumberValue(5.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument(f"off_atten", NumberValue(5, min=1.0, max=30), "parameters")
        self.setattr_argument(f"off_scale", NumberValue(0.5, min=0.0, max=0.9), "parameters")
        self.setattr_argument("off_time",
                      NumberValue(0.0*1e-3,min=0.0,max=200.00*1e-3,scale = 1e-3,
                       unit="ms"), "parameters")
        self.setattr_argument("load_time", NumberValue(10.0*1e-3,min=0.0*1e-3,max=50.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")

    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms(int(self.pulses*1.2))
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()

        # Initialize camera
        self.Camera.camera_init()



    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)
        
        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)

        # for _ in range(int(self.pulses)):
        for t in [0,1,2,3,4,5,6,7,8]:
            self.Camera.arm()
            delay(200*ms)
            
            self.MOTs.rMOT_pulse()
            delay(self.load_time) ##load into dipole trap if desired
            
            
            self.Bragg.set_AOM_attens([("Dipole",self.off_atten ), ("Homodyne",self.off_atten)])
            self.Bragg.set_AOM_scales([("Dipole",self.off_scale ), ("Homodyne",self.off_scale)])
            
            for _ in range(t):
                delay(self.off_time)
            
            self.Bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",3.0)])  
            self.Bragg.set_AOM_scales([("Dipole",0.8 ), ("Homodyne",0.8)]) 
            
            delay(self.image_wait_time)
            
            

            self.MOTs.take_MOT_image(self.Camera)
            delay(50*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])


            delay(100*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()
