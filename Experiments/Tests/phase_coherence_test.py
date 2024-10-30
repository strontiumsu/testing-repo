# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 18:16:51 2024

@author: ejporter
"""


from scan_framework import Scan1D, TimeFreqScan
from artiq.coredevice import ad9910
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import *
# imports
import numpy as np
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel


class phase_coherence_test(Scan1D, TimeFreqScan, EnvExperiment):

    def build(self, **kwargs):

        super().build(**kwargs)
        self.setattr_device("ttl1") # triggering pulse
        self.Bragg = _Bragg(self)

        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times = {'start':0*ms,
            'stop':2000*ms,
            'npoints':20,
            'unit':"ms",
            'scale':ms,
            'global_step':0.1*ms,
            'ndecimals':2},
             frequencies={
            'start':-1000*kHz,
            'stop':1000*kHz,
            'npoints':50,
            'unit':"kHz",
            'scale':kHz,
            'global_step':0.1*kHz,
            'ndecimals':3},
            frequency_center={'default':100.043*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}

            )

        self.B1_dds = self.Bragg.urukul_channels[1]
        self.B2_dds = self.Bragg.urukul_channels[2]



    def prepare(self):
        self.Bragg.prepare_aoms() # custom class for AOM functions
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=True)

    @kernel
    def before_scan(self):
        self.core.reset()

        self.ttl1.output()
        self.Bragg.init_aoms(on=True)
        delay(2*ms)
        self.B1_dds.sw.off()
        self.B2_dds.sw.off()
        delay(1*ms)
        self.B1_dds.set_phase_mode(2)
        self.B2_dds.set_phase_mode(2)
        delay(1*ms)
        self.core.wait_until_mu(now_mu())


    @kernel
    def measure(self, time, frequency):
        pulse_time = time
        freq = frequency

        p = time/(1*ms)
        f = 100*MHz + 50*MHz*p

        self.core.reset()
        delay(10* ms)
        t = now_mu()
        self.B2_dds.set(frequency=100*MHz, amplitude=0.8, phase=0.0, ref_time_mu=t, phase_mode=ad9910.PHASE_MODE_ABSOLUTE)
        self.B1_dds.set(frequency=100*MHz, amplitude=0.8, phase=0.0, ref_time_mu=t, phase_mode=ad9910.PHASE_MODE_ABSOLUTE)


        delay(1*ms)


        self.B1_dds.sw.on()
        self.B2_dds.sw.on()
        self.ttl1.on()
        delay(1*ms)
        self.B1_dds.sw.off()
        self.B2_dds.sw.off()

        with parallel:
            delay(10*ms)
            self.B2_dds.set_mu(self.B2_dds.frequency_to_ftw(200*MHz), asf=self.B2_dds.amplitude_to_asf(0.8))
            self.B1_dds.set(frequency=100*MHz, amplitude=0.8, phase=0.0)
        delay(1*ms)
        self.B1_dds.sw.on()
        self.B2_dds.sw.on()

        delay(1*ms)
        self.B1_dds.sw.off()
        self.B2_dds.sw.off()
        self.ttl1.off()






        delay(200*ms)
        self.core.wait_until_mu(now_mu())

        return 0
