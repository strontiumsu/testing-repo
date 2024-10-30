# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 17:12:24 2024

@author: R. Knight
"""



from artiq.experiment import *

# imports
import numpy as np
from CoolingClass import _Cooling
from NewCamera import _Camera2


class MOTloadingtime_exp(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.MOTs = _Cooling(self)
        self.Camera = _Camera2(self)


        # attributes for this experiment
        ###
        self.setattr_argument("load_time", Scannable(default=[RangeScan(10*1e-3,
                     2000*1e-3,20, randomize=False), NoScan(1000*1e-3)], scale=1e-3, unit='ms'),"parameters")
        self.setattr_argument("wait_time", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")



    def prepare(self):
        # initial datasets for the aoms and mot coils, does not run on core
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        self.load_scan = list(self.load_time) # turn into iterable


    @kernel
    def run(self):
        # initial devices
        self.core.reset()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        delay(5*ms)

        self.Camera.arm(N=2*len(self.load_scan))
        delay(200*ms)


        for delay_time in self.load_scan:

            self.MOTs.atom_source_on()
            self.MOTs.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
            self.MOTs.set_current_dir(0)
            self.MOTs.Blackman_ramp_up()

            delay(delay_time)
            self.MOTs.take_MOT_image(self.Camera)

            self.MOTs.Blackman_ramp_down()
            self.MOTs.atom_source_off()
            self.MOTs.AOMs_off(["3D", "3P0_repump", "3P2_repump"])
            delay(5*ms)

            self.MOTs.take_MOT_image(self.Camera)
            delay(50*ms)

            self.Camera.process_image(bg_sub=True)

            delay(self.wait_time)
