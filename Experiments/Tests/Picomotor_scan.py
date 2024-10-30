# # -*- coding: utf-8 -*-
# """
# Created on Wed Mar 15 16:01:28 2023

# @author: E. Porter
# """

from scan_framework import Scan2D, TimeScan
from artiq.experiment import *
import numpy as np
import time


# from CoolingClass import _Cooling
# from ThreePhotonClass import _ThreePhoton
from PicomotorClass import _Picomotor
from repository.models.scan_models import RamseyPhaseModel


class Picomotor_scan(Scan2D, EnvExperiment):


    def build(self, **kwargs):

        super().build(**kwargs)
        self.Pico = _Picomotor(self)
        self.setattr_device("ttl4")

        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.setattr_argument('step1', Scannable(
            default=RangeScan(
                start=0,
                stop=10,
                npoints=20
            ),
            scale=1,
            ndecimals=0,
            global_step=1
        ), group='Scan Range')
        self.setattr_argument('step2', Scannable(
            default=RangeScan(
                start=0,
                stop=10,
                npoints=50
            ),
            scale=1 ,
            ndecimals=0,
            global_step=1
        ), group='Scan Range')


        # scan arguments
        self.scan_arguments(nbins={'default':1000},
                            nrepeats={'default':1},
                            npasses={'default':1},
                            fit_options={'default':"Fit and Save"})

    def get_scan_points(self):
        return [self.step1, self.step2]

    @kernel
    def set_scan_point(self, i_point, point):
        x_pos = point[0]
        y_pos = point[1]

        # set the trap frequency at the start of the tickle sub-scan
        self.Pico.set_position(1, int(x_pos))
        self.Pico.set_position(2, int(y_pos))
        self.core.break_realtime()

    def prepare(self):
        #prepare/initialize mot hardware and camera
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.ThPh.prepare_aoms()
        # register model with scan framework
        self.enable_histograms = True
        self.model1 = RamseyPhaseModel(self)  # change model
        self.model2 = RamseyPhaseModel(self)   # change model
        self.register_model(self.model1, dimension=0, fit=True, set=True)
        self.register_model(self.model2, dimension=1, fit=True, set=True, measurement=True)
        self.Pico.set_home(1)
        self.Pico.set_home(2)  # change how this works so we keep our home consistent

    @kernel
    def before_scan(self):
        # runs before experiment take place

        #initialize devices on host
        self.core.reset()

        # intialize everything
        delay(10*ms)

    @kernel
    def after_scan(self):
        self.Pico.set_position(1, 0)
        self.Pico.set_position(2, 0)

    @kernel
    def measure(self, point):
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(2000*ms)
        return int(1e5*np.sin(point[1]*point[0]/1000))



    def calculate_dim0(self, dim1_model):
        param = dim1_model.fit.params.f
        # weight final fit by error in this dimension 1 fit param
        error = dim1_model.fit.errs.f_err
        return param, 0.01
