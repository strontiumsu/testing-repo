# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 09:16:50 2024

@author: sr
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


class DDS_profile_scanning_test_exp(Scan1D, TimeFreqScan, EnvExperiment):

    def build(self, **kwargs):

        super().build(**kwargs)
        self.setattr_device("ttl1") # triggering pulse
        self.Bragg = _Bragg(self)
        self.scan_dds = self.Bragg.urukul_channels[1] # easy access to channel 1 for scan

        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(times = {'start':0*us,
            'stop':2000*us,
            'npoints':20,
            'unit':"us",
            'scale':us,
            'global_step':0.1*us,
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

        self.freq_chirp = 42.5509*GHz # per second
        self.profiles = 3
        self.RAM_size = int(1024/self.profiles)


        self.freq_list1= np.linspace(100.0*MHz, 100.0*MHz, self.RAM_size)    # just initialize randomly
        self.freq_list2= np.linspace(100.0*MHz, 100.0*MHz, self.RAM_size)
        self.freq_list3= np.linspace(100.0*MHz, 100.0*MHz, self.RAM_size)


        self.freq_list_ram = [np.full(self.RAM_size, 1),np.full(self.RAM_size, 1),np.full(self.RAM_size, 1)]

        self.step_size=0 # just initialize to anything (int)

        self.setattr_argument(f"freq_range", NumberValue(100*1e3, min=0*1e3, max=50000*1e3, scale=1e3, unit='kHz'),  "parameters")
        self.setattr_argument("interrogation_time", NumberValue(20.0*1e-6,min=1.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")


    def prepare(self):
        self.Bragg.prepare_aoms() # custom class for AOM functions
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=True)

    @kernel
    def before_scan(self):
        self.core.reset()

        self.ttl1.output()
        self.Bragg.init_aoms(on=False)

        self.scan_dds.sw.off()
        delay(1*ms)
        self.core.wait_until_mu(now_mu())

    @kernel
    def prepare_freq_ramp(self, t, f):
        self.step_size = int(t/(self.RAM_size*4*ns))
        p_time = self.step_size*self.RAM_size*4*ns # discritization correct
        f0 = f+self.freq_range/2

        f0_1 = f0 + 0
        f0_2 = f0 + (p_time+self.interrogation_time)*self.freq_chirp
        f0_3 = f0 + 2*(p_time+self.interrogation_time)*self.freq_chirp


        f_step = self.freq_range/(self.RAM_size-1)

        for i in range(self.RAM_size):
            self.freq_list1[i] = f0_1-f_step*i+self.step_size*i*4*ns*self.freq_chirp
            self.freq_list2[i] = f0_2-f_step*i+self.step_size*i*4*ns*self.freq_chirp
            self.freq_list3[i] = f0_3-f_step*i+self.step_size*i*4*ns*self.freq_chirp


        self.scan_dds.frequency_to_ram(self.freq_list1, self.freq_list_ram[0])
        self.scan_dds.frequency_to_ram(self.freq_list2, self.freq_list_ram[1])
        self.scan_dds.frequency_to_ram(self.freq_list3, self.freq_list_ram[2])


        self.core.break_realtime()
        delay(50 * ms)
        self.scan_dds.set(f-self.freq_range/2, amplitude=self.Bragg.scale_Bragg1)
        delay(1 * ms)

        self.scan_dds.set_cfr1(ram_enable=0)    # turn off ram enable
        self.scan_dds.cpld.io_update.pulse_mu(8)
        delay(10*us)

        for i in range(self.profiles):
            self.scan_dds.set_profile_ram(start=i*self.RAM_size, end=(i+1)*self.RAM_size-1, step=(self.step_size | (2**6 - 1 ) << 16),
                                      profile=i, mode=ad9910.RAM_MODE_RAMPUP)
            self.scan_dds.cpld.set_profile(i)
            delay(10*us)
            delay(10*us)
            self.scan_dds.cpld.io_update.pulse_mu(8)
            delay(10*ms)
            delay(10*us)
            self.scan_dds.write_ram(self.freq_list_ram[i])
            delay(10 * us)

        self.scan_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW)
        delay(10*us)
        self.scan_dds.cpld.set_profile(0)

        self.core.wait_until_mu(now_mu())
    @kernel
    def measure(self, time, frequency):
        pulse_time = time
        freq = frequency

        self.core.reset()
        delay(1 * ms)

        for _ in range(10):
            self.ttl1.pulse(pulse_time)
            delay(self.interrogation_time)








        # self.prepare_freq_ramp(pulse_time, freq)
        # delay(1 * ms)


        # pulse_time = self.step_size*self.RAM_size*4*ns
        # delay(10 * ms)

        # with parallel:  # turn on pulse
             # self.scan_dds.cpld.io_update.pulse_mu(8)
             # self.scan_dds.sw.on()
        # self.ttl1.on()

        # delay(pulse_time) # wait


        # self.scan_dds.sw.off()
        # self.ttl1.off()
        # self.scan_dds.set_cfr1(ram_enable=0)


        # with parallel:
        # delay(self.interrogation_time)
        #     with sequential:
        #         self.scan_dds.cpld.io_update.pulse_mu(8)
        #         self.scan_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW)
        #         self.scan_dds.cpld.set_profile(1)

        # with parallel:  # turn on pulse
        #      # self.scan_dds.cpld.io_update.pulse_mu(8)
        #      self.scan_dds.sw.on()
              # self.ttl1.on()

        # delay(pulse_time) # wait
        #

        # self.scan_dds.sw.off()
        # self.ttl1.off()
        # # self.scan_dds.set_cfr1(ram_enable=0)


        # with parallel:
        # delay(self.interrogation_time)
        #     with sequential:
        #         self.scan_dds.cpld.io_update.pulse_mu(8)
        #         self.scan_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW)
        #         self.scan_dds.cpld.set_profile(2)

        # with parallel:  # turn on pulse
        #      self.scan_dds.cpld.io_update.pulse_mu(8)
        #      self.scan_dds.sw.on()
        # self.ttl1.on()

        # delay(pulse_time) # wait


        # self.scan_dds.sw.off()
        # self.ttl1.off()




        delay(1000*ms)
        self.core.wait_until_mu(now_mu())

        return 0
