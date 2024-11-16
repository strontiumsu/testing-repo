# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us

from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, sequential, now_mu,BooleanValue, MHz

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera


class Red_MOT_Optimization_exp(EnvExperiment):
    """
    Red_MOT_Optimization_exp
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


        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=0.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("broadband",BooleanValue(False),"parameters")


    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()

        # Initialize camera
        self.Camera.camera_init()

        self.Camera.prep_datasets(np.full(int(self.pulses), np.nan))

    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)

        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)
        ## MAIN EPERIMENT LOOP
        
        ff = 180*MHz
        If = 21.0
        fstart = 178*MHz
        Istart = 11.0
            
        for i in range(int(self.pulses)): #scan for intensity
            I0 = Istart+i*(If-Istart)/int(self.pulses)
            for j in range(int(self.pulses)): #scan for frequency
                self.Camera.arm()
                delay(200*ms)
                f0 = fstart+j*(ff-fstart)/(int(self.pulses))
    
                self.MOTs.rMOT_pulse(sf=False)
                # self.MOTs.set_current(self.MOTs.rmot_sf_current)
                
                # #############################
                # # set start detuning and frequency
                # #f0 = 179*MHz
                # #I0 = 12.0
                
                # # perform the scan over both
                # ### Ramp transfer sequence
                # tramp = 50*ms
                # dt = tramp/int(self.MOTs.Npoints)
                # self.MOTs.AOMs_on(["Probe"])
                # for step in range(1, int(self.MOTs.Npoints)):
                #     self.MOTs.set_AOM_attens([("Probe",I0+(If-I0)*step/int(self.MOTs.Npoints))])
                #     self.MOTs.set_AOM_freqs([("Probe",f0+(ff-f0)*step/int(self.MOTs.Npoints))])
                #     delay(dt)
                # self.MOTs.AOMs_off(["Probe"])
                
                #############################
    
                ## image and proess
                self.MOTs.take_MOT_image(self.Camera)
                delay(10*ms)
                self.Camera.process_image(bg_sub=True)
                delay(300*ms)
                self.core.wait_until_mu(now_mu())
                delay(200*ms)
                self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])
    
                #self.Camera.get_count_stats(m)
        ######################

        self.MOTs.set_AOM_attens([("Probe",23.5)])

        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump', '3D',"Probe"])
        self.MOTs.atom_source_on()
