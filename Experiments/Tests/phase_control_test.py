# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 11:07:04 2024

@author: ejporter
"""

from scan_framework import Scan1D
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import *

# imports
import numpy as np
import pyvisa
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING
from artiq.coredevice import ad9910



class phase_control_test_exp(Scan1D, EnvExperiment):

    def build(self, **kwargs):
    # required initializations

        super().build(**kwargs)
        self.setattr_device("ttl1")  # trigger for function generator

        # import classes for experiment control

        self.Bragg = _Bragg(self)
        self.chirp_dds = self.Bragg.urukul_channels[1]

        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks

        self.scan_arguments(nbins={'default':1000},
                    nrepeats={'default':1},
                    npasses={'default':1},
                    fit_options={'default':"No Fits"})

        self.setattr_argument('pulse_phase',
            Scannable(default=RangeScan(
            start=0.0,
            stop=2.0,
            npoints=20),
            scale=1,
            ndecimals=2,
            unit="Turns"), 'parameters')


        self.setattr_argument("int_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("vel_sel_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("vel_sel_delay", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("pi_2_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("pi_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")


        # self.doppler_chirp_rate = 42.5509*MHz
        self.doppler_chirp_rate = 148.5509*GHz

        self.freq_list= np.linspace(100.0*MHz, 100.0*MHz, 1024)
        self.freq_list_ram = np.full(1024, 1)
        self.step_size=0

        self.exp_length = 0.0*us

    def prepare(self):
        self.Bragg.prepare_aoms()

    def get_scan_points(self):
        return self.pulse_phase



    def prepare(self):
    #prepare/initialize mot hardware and camera

        self.Bragg.prepare_aoms()
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=False)


    @kernel
    def before_scan(self):
        self.exp_length = self.vel_sel_time + self.vel_sel_delay + 2*self.pi_2_time + 2* self.int_time + self.pi_time

        self.core.reset()
        delay(1*ms)
        self.ttl1.output()
        self.Bragg.init_aoms(on=True)
        self.Bragg.AOMs_off(["Bragg1", "Bragg2"])
        self.core.wait_until_mu(now_mu())

    @kernel
    def set_phases(self, phase, t0):

        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+10*MHz, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+10*MHz, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+20*MHz, phase, t0, 3)

        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 3)

        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 3)

        self.core.wait_until_mu(now_mu())




    @kernel
    def measure(self, point):
        phase = point
        ## prepare
        self.core.reset()
        delay(1*ms)
        self.core.break_realtime()
        delay(250*ms)

        t0 = now_mu()
        self.set_phases(phase, t0)

        delay(100*ms)
        self.load_gravity_chrip(self.exp_length, phase, t0)


        self.core.wait_until_mu(now_mu())
        delay(100*ms)




        self.ttl1.on()

        ## EXP START
        with parallel:
            self.Bragg.bragg_pulse(self.vel_sel_time)
            self.chirp_dds.cpld.io_update.pulse_mu(8)
        with parallel:
            delay(self.vel_sel_delay)
            self.Bragg.switch_profile(1, dds_num = 2)

        self.Bragg.bragg_pulse(self.pi_2_time)
        with parallel:
            delay(self.int_time)
            self.Bragg.switch_profile(2, dds_num = 2)
        self.Bragg.bragg_pulse(self.pi_time)


        with parallel:
            delay(self.int_time)
            self.Bragg.switch_profile(3, dds_num = 2)

        self.Bragg.bragg_pulse(self.pi_2_time)
        ## EXP END


        self.ttl1.off()

        self.chirp_dds.set_cfr1(ram_enable=0)
        self.chirp_dds.cpld.io_update.pulse_mu(8)
        delay(10*ms)



        # self.Bragg.switch_profile(0, dds_num=2)
        delay(200*ms)
        self.core.wait_until_mu(now_mu())
        delay(200*ms)
        return 0




    @kernel
    def load_gravity_chrip(self, length, phase, t0):

        # loads frequency list
        self.step_size = int(length/(1024*4*ns))
        f_range = length*self.doppler_chirp_rate
        f0 = self.Bragg.freq_Bragg1
        f_step  = f_range/1023
        for i in range(1024):
            self.freq_list[1023-i] = f0+f_step*i


        self.chirp_dds.frequency_to_ram(self.freq_list, self.freq_list_ram)
        self.core.break_realtime()

        self.chirp_dds.set(f0, amplitude=self.Bragg.scale_Bragg1, phase=0.0, phase_mode=PHASE_MODE_TRACKING, ref_time_mu=t0, profile=0)
        delay(1 * ms)

        self.chirp_dds.set_cfr1(ram_enable=0)
        self.chirp_dds.cpld.io_update.pulse_mu(8)

        self.chirp_dds.set_profile_ram(start=0, end=1024-1, step=(self.step_size | (2**6 - 1 ) << 16),
                                  profile=0, mode=ad9910.RAM_MODE_RAMPUP)
        self.chirp_dds.cpld.set_profile(0)
        delay(10*us)

        self.chirp_dds.cpld.io_update.pulse_mu(8)
        delay(10*us)

        self.chirp_dds.write_ram(self.freq_list_ram)
        delay(10 * us)

        self.chirp_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW) # gets the chirp ready to pulse
        delay(10*ms)




        self.core.wait_until_mu(now_mu())
