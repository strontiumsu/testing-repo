# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 11:02:56 2023

@author: sr
"""


from artiq.experiment import EnvExperiment, BooleanValue, kernel, now_mu, ms, NumberValue, delay, parallel, sequential

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg


class Bragg_pulse_test(EnvExperiment):
    """
    Bragg_pulse_test
    This experiment uses the CoolingClass and BraggClass to control the relevant AOMs and MOT
    coils to pulse the blue MOT off and on.

    """
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)



        # attributes for this experiment
        self.setattr_argument("pulses", NumberValue(5,min=0, max=100), "parameters")
        self.setattr_argument("dipole_load_time", NumberValue(100.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("max_pulse_time", NumberValue(500.0*1e-6,min=0.0*1e-6,max=5000.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("drift_time", NumberValue(5.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")

    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
                # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms(int(self.pulses*1.2))
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()

        # Initialize camera
        self.Camera.camera_init()

    @kernel
    def run(self):
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)

        self.MOTs.set_current_dir(0)
        delay(10*ms)

        self.Bragg.AOMs_off(['Bragg1', 'Bragg2'])

        delay(10*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(100*ms)

        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump", "Probe"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump", "Probe"])
        self.MOTs.atom_source_off()

        for i in range(int(self.pulses)):

            delay(100*ms)
            self.Camera.arm()
            delay(200*ms)

            self.Bragg.set_AOM_freqs([("Bragg2",(110.0 - 0.3 +(0.01*i))*10**6)])

            self.MOTs.AOMs_off(self.MOTs.AOMs)
            delay(15*ms)
            self.MOTs.rMOT_pulse()
            with parallel:
                delay(self.dipole_load_time)
                with sequential:
                    self.MOTs.set_current_dir(1) # XXX let MOT field go to zero and switch H-bridge, 5ms
                    self.MOTs.set_current(0.3)
            self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
            self.Bragg.set_AOM_scales([("Dipole",0.2 ), ("Homodyne",0.2)])
            self.Bragg.AOMs_off(['Homodyne'])

            self.Bragg.bragg_pulse(self.max_pulse_time)

            with parallel:
                delay(self.drift_time)
                with sequential:
                    self.MOTs.set_current(0.0)
                    self.MOTs.set_current_dir(0)
            self.MOTs.take_MOT_image(self.Camera)
            self.Bragg.set_AOM_attens([("Dipole",4.0 ), ("Homodyne",self.Bragg.atten_Homodyne)])
            self.Bragg.set_AOM_scales([("Dipole",0.8 ), ("Homodyne",self.Bragg.scale_Homodyne)])
            self.Bragg.AOMs_on(['Homodyne'])


            delay(50*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D', "Probe"])
            delay(200*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()
