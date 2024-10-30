# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")
from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, sequential, now_mu,BooleanValue

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg

class Red_MOT_Molasses_exp(EnvExperiment):
    """
    Red_MOT_molasses_exp
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
        self.setattr_argument("molasses_time", NumberValue(10.0*1e-3,min=0.0*1e-3,max=500.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("molasses",BooleanValue(False),"parameters")


    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()

        # Initialize camera
        self.Camera.camera_init()

        self.Camera.prep_datasets(np.full(int(self.pulses), np.nan))

    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)
        self.Bragg.AOMs_off(["Bragg1", "Bragg2"])

        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)
        for m in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)

            self.MOTs.rMOT_pulse()
            delay(10*ms)
            if self.molasses:
                self.MOTs.rMOT_beam_pulse(self.molasses_time)
            self.Bragg.set_AOM_attens([("Homodyne",30.0)])
            self.Bragg.set_AOM_scales([("Homodyne",0.5)])
            delay(self.wait_time)


            self.MOTs.take_MOT_image(self.Camera)
            delay(10*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])

            #self.Camera.get_count_stats(m)
            delay(self.wait_time)
            self.Bragg.set_AOM_attens([("Homodyne",self.Bragg.atten_Homodyne)])
            self.Bragg.set_AOM_scales([("Homodyne",self.Bragg.scale_Homodyne)])

        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump', '3D',"Probe"])
        self.MOTs.atom_source_on()
