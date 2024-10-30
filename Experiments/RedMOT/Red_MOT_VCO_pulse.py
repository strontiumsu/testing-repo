# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author:
"""

# make available artiq classes for us

from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, sequential, now_mu,BooleanValue, kHz

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg


class Red_MOT_VCO_pulse_exp(EnvExperiment):
    """
    Red_MOT_VCO_pulse_exp
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
        self.setattr_argument("sf",BooleanValue(False),"parameters")
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

        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)
        for m in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)

            self.MOTs.set_AOM_freqs([("Probe",self.MOTs.freq_Probe)])
            self.MOTs.set_AOM_attens([("Probe",self.MOTs.atten_Probe)])

            self.MOTs.rMOT_VCO_pulse(self.sf)

            #delay(5*ms)
            if self.molasses:
                self.MOTs.set_AOM_freqs([("Probe",self.MOTs.freq_Probe+400*kHz)])
                self.MOTs.set_AOM_attens([("Probe",14.0+15.0*m/int(self.pulses))])
                self.MOTs.AOMs_on(["Probe"])
            #delay(10*ms)
            #self.MOTs.AOMs_off(["Probe"])

            ## ramp down lattice
            self.Bragg.lattice_rampdown(30.0,1*ms)

            delay(self.wait_time)


            self.Bragg.set_AOM_attens([("Homodyne",self.Bragg.atten_Homodyne)])

            self.MOTs.take_MOT_image(self.Camera)
            delay(10*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])

            #self.Camera.get_count_stats(m)
            delay(self.wait_time)

        self.MOTs.AOMs_on(['3P0_repump', '3P2_repump', '3D',"Probe"])
        self.MOTs.atom_source_on()
