# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

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

class Cavity_Scan_Repeat_exp(EnvExperiment):
    """
    Cavity_Scan_Repeat_exp
    This experiment uses the CoolingClass to control the relevant AOMs and MOT
    coils to pulse the Red MOT off and on, taking an image each time to display to the user
    at detection.images.current_image.

    parameters:
        <all parameters inherited from CoolingClass>
        <all parameters inherited from Detection2>
        pulses: number of times to pulse the red MOT
        wait_time: how long to wait between pulses

    """

    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)

        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("push_beam",BooleanValue(False),"parameters")


    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
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

        for m in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)
            self.MOTs.rMOT_pulse()
            # delay(5*ms)
            # self.MOTs.set_current_dir(1)
            # self.MOTs.set_current(0.2)
            
            delay(self.wait_time) ##load into dipole trap if desired
            
            #drop atoms
            #self.Bragg.set_AOM_attens([("Homodyne",30.0)])
            #delay(5*ms)
            
            #move atoms
            #self.Bragg.set_AOM_freqs([("Homodyne",79.9*10**6)])
            #delay(5*ms)
            #self.MOTs.cavity_ramp(0.8, 5*ms, 51)
            self.MOTs.cavity_scan_trig()
            delay(0.50*ms)
            self.MOTs.cavity_scan_trig()
            
            
            if self.push_beam:
                self.MOTs.push()
            
            self.MOTs.set_current(0.0)
            self.MOTs.take_MOT_image(self.Camera)
            delay(10*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])
            self.Bragg.set_AOM_attens([("Homodyne",3.0)])
            self.Bragg.set_AOM_freqs([("Homodyne",80.0*10**6)])
            #self.Camera.get_count_stats(m)
            self.MOTs.set_current_dir(0)
            delay(self.wait_time)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()
