# -*- coding: utf-8 -*-
"""
Created on Thu Feb  2 11:17:41 2023

@author: E. Porter
"""

# make available artiq classes for us
from artiq.experiment import EnvExperiment, kernel, ms,us, NumberValue, delay, parallel, sequential, now_mu,BooleanValue

# imports
import numpy as np
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg

class Cavity_Scan_exp(EnvExperiment):

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
        self.setattr_argument("drop_time", NumberValue(1.0*1e-3,min=0.0*1e-3,max=20.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("drop",BooleanValue(False),"parameters")


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
        self.MOTs.AOMs_off(['Probe']) #turn off probe beam
        delay(50*ms)
        self.MOTs.take_background_image_exp(self.Camera)
        delay(500*ms)

        # set cavity scan triger to zero
        self.MOTs.dac_0.write_dac(3, 0.0)
        self.MOTs.dac_0.load()
        delay(5*ms)


        for m in range(int(self.pulses)):
            self.Camera.arm()
            delay(200*ms)
            self.MOTs.rMOT_pulse()
            # delay(5*ms)
            self.MOTs.set_current_dir(1)
            self.MOTs.set_current(0.5)

            delay(self.wait_time) ##load into dipole trap if desired

            #drop atoms
            # if self.drop:
            #     self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
            #     self.Bragg.set_AOM_scales([("Dipole",0.6 ), ("Homodyne",0.1)])
            #     self.Bragg.AOMs_off(['Homodyne'])
            #     delay(1*ms)
            #     self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",self.Bragg.atten_Homodyne)])
            #     self.Bragg.set_AOM_scales([("Dipole",self.Bragg.scale_Dipole ), ("Homodyne",self.Bragg.scale_Homodyne)])
            #     delay(self.drop_time)

            self.Bragg.set_AOM_attens([("Dipole",12.0 ), ("Homodyne",30.0)])
            self.Bragg.set_AOM_scales([("Dipole",0.8 ), ("Homodyne",0.1)])
            self.Bragg.AOMs_off(['Homodyne'])
            #delay(self.drop_time*m/int(self.pulses))

            #scan cavity resonance
            # Scan the cavity probe
            self.MOTs.AOMs_on(['Probe'])# turn probe beam on
            self.MOTs.dac_0.write_dac(3, 5.0) #trigger scan
            self.MOTs.dac_0.load()
            delay(3*ms)
            self.MOTs.AOMs_off(['Probe']) #turn off probe beam

            self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",self.Bragg.atten_Homodyne)])
            self.Bragg.set_AOM_scales([("Dipole",self.Bragg.scale_Dipole ), ("Homodyne",self.Bragg.scale_Homodyne)])


            self.MOTs.set_current(0.0)
            self.MOTs.take_MOT_image(self.Camera)
            delay(10*ms)
            self.Camera.process_image(bg_sub=True)
            delay(300*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D'])
            self.Bragg.AOMs_on(['Homodyne'])

            #reset Cavity scan trigger to 0
            delay(5*ms)
            self.MOTs.dac_0.write_dac(3, 0.0)
            self.MOTs.dac_0.load()

            
            self.MOTs.set_current_dir(0)
            delay(self.wait_time)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()
