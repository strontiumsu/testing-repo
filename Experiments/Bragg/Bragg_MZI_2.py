# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 17:23:11 2024

@author: ejporter
"""

from scan_framework import Scan1D, TimeFreqScan
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")

from artiq.experiment import *

# imports
import numpy as np
import pyvisa
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING
from AWG import WaveformGenerator


class Bragg_MZI_2_exp(Scan1D, EnvExperiment):

    def build(self, **kwargs):
    # required initializations

        super().build(**kwargs)
        self.setattr_device("ttl1")  # trigger for function generator

        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)

        self.rigol= None

        # attributes here
        self.enable_pausing = True # disable to speed up by not checking scheduler
        self.enable_auto_tracking=False
        self.enable_profiling = False # enable to print runtime statistics to find bottlenecks
        self.wg = WaveformGenerator()





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

        self.setattr_argument("dipole_load_time", NumberValue(15.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("drift_time", NumberValue(20.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")

        self.setattr_argument("vel_sel_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("vel_sel_amp", NumberValue(0.5,min=0.0,max=1.0,scale=1,
               unit="V"),"parameters")



        self.setattr_argument("vel_sel_delay", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")




        self.setattr_argument("pi_2_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("pi_2_amp", NumberValue(0.5,min=0.0,max=1.0,scale=1,
               unit="V"),"parameters")

        self.setattr_argument("pi_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")
        self.setattr_argument("pi_amp", NumberValue(0.5,min=0.0,max=1.0,scale=1,
               unit="V"),"parameters")

        self.setattr_argument("int_time", NumberValue(20.0*1e-6,min=0.0*1e-6,max=500.00*1e-6,scale=1e-6,
               unit="us"),"parameters")


        self.setattr_argument("MZ_freq", NumberValue(100.0*1e3,min=0.0*1e3,max=5000.00*1e3,scale=1e3,
               unit="kHz"),"parameters")


        self.vel_sel_det = 42.8*kHz
        self.doppler_rate = 42.5509*MHz
        # self.doppler_rate= 0


    def get_scan_points(self):
        return self.pulse_phase

    @kernel
    def set_phases(self, phase):

        t0 = now_mu()
        self.Bragg.set_AOM_phase('Bragg1', self.Bragg.freq_Bragg1 , 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Bragg1', self.Bragg.freq_Bragg1 - (self.vel_sel_time+self.vel_sel_delay)*self.doppler_rate, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Bragg1', self.Bragg.freq_Bragg1- (self.vel_sel_time+self.vel_sel_delay + self.pi_2_time+self.int_time)*self.doppler_rate, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Bragg1', self.Bragg.freq_Bragg1- (self.vel_sel_time+self.vel_sel_delay + self.pi_2_time+2*self.int_time+self.pi_time)*self.doppler_rate, 0.0, t0, 3)

        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+self.vel_sel_det, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+self.MZ_freq, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+self.MZ_freq, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Bragg2', self.Bragg.freq_Bragg2+self.MZ_freq, phase, t0, 3)

        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Dipole', self.Bragg.freq_Dipole, 0.0, t0, 3)

        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 0)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 1)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 2)
        self.Bragg.set_AOM_phase('Homodyne', self.Bragg.freq_Homodyne, 0.0, t0, 3)

    @kernel
    def measure(self, point):

        phase = point

        self.core.reset()
        delay(1*ms)
        self.core.break_realtime()
        delay(250*ms)



        self.set_phases(phase)
        delay(1*ms)

        self.Bragg.switch_profile(0)

        delay(20*ms)
        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)


        self.MOTs.rMOT_pulse()
        delay(self.dipole_load_time)

        self.Bragg.set_AOM_attens([("Dipole",30.0), ("Homodyne",30.0)])
        self.Bragg.set_AOM_scales([("Dipole",0.6), ("Homodyne",0.1)])
        self.Bragg.AOMs_off(['Homodyne'])

        self.ttl1.on()

        ## EXP START
        self.Bragg.bragg_pulse(self.vel_sel_time)
        with parallel:
            delay(self.vel_sel_delay)
            self.Bragg.switch_profile(1)

        self.Bragg.bragg_pulse(self.pi_2_time)
        with parallel:
            delay(self.int_time)
            self.Bragg.switch_profile(2)
        self.Bragg.bragg_pulse(self.pi_time)


        with parallel:
            delay(self.int_time)
            self.Bragg.switch_profile(3)

        self.Bragg.bragg_pulse(self.pi_2_time)
        ## EXP END


        self.ttl1.off()




        self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole), ("Homodyne",30.0)])  # keeping on dipole guide
        self.Bragg.set_AOM_scales([("Dipole",self.Bragg.scale_Dipole)])

        delay(self.drift_time)

        self.MOTs.take_MOT_image(self.Camera)
        self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",self.Bragg.atten_Homodyne)])
        self.Bragg.set_AOM_scales([("Dipole",self.Bragg.scale_Dipole ), ("Homodyne",self.Bragg.scale_Homodyne)])
        self.Bragg.AOMs_on(['Homodyne'])


        delay(50*ms)
        self.Camera.process_image(bg_sub=True)
        delay(400*ms)
        self.core.wait_until_mu(now_mu())
        delay(200*ms)
        self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D', "Probe"])
        delay(200*ms)
        self.Bragg.switch_profile(0)
        delay(1*ms)

        return 0


    def prepare(self):
    #prepare/initialize mot hardware and camera
        self.prepare_rigol()
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Bragg.prepare_aoms()
        self.Camera.camera_init()

        # register model with scan framework
        self.enable_histograms = True
        self.model = RabiModel(self)
        self.register_model(self.model, measurement=True, fit=False)


    @kernel
    def before_scan(self):
        self.core.reset()
        delay(1*ms)
        self.ttl1.output()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)
        self.Bragg.AOMs_off(["Bragg1", "Bragg2"])

        self.MOTs.set_current_dir(0)
        delay(10*ms)


        self.MOTs.take_background_image_exp(self.Camera)
        delay(100*ms)

        self.MOTs.warm_up_MOTs()
        delay(10*ms)
        self.core.wait_until_mu(now_mu())




    def before_measure(self, point, measurement):


        LENGTH = self.vel_sel_time + self.vel_sel_delay + 2*self.pi_2_time + self.pi_time + 2*self.int_time
        SAMPLES = 6000
        SAMPLE_RATE = SAMPLES/LENGTH

        self.wg.sample_rate = SAMPLE_RATE


        self.wg.reset_waveform()

        t_now = 0
        self.wg.add_gaussian_pulse(t_now, self.vel_sel_time, self.vel_sel_amp, self.vel_sel_time/7)

        t_now += self.vel_sel_time + self.vel_sel_delay
        self.wg.add_gaussian_pulse(t_now, self.pi_2_time, self.pi_2_amp, self.pi_2_time/7)

        t_now += self.pi_2_time + self.int_time
        self.wg.add_gaussian_pulse(t_now, self.pi_time, self.pi_amp, self.pi_time/7)

        t_now += self.pi_time + self.int_time
        self.wg.add_gaussian_pulse(t_now, self.pi_2_time, self.pi_2_amp, self.pi_2_time/7)


        t, y = self.wg.get_waveform()
        val_str = ",".join(map(str, y))

        self.rigol.write(":OUTP1 OFF");

        self.rigol.write(":TRACE:DATA VOLATILE," + val_str)
        self.rigol.write(f":SOUR1:APPL:USER {1/LENGTH}, {2*self.wg.max}, 0, 0")

        self.rigol.write("SOUR1:BURS ON")
        self.rigol.write("SOUR1:BURS:MODE TRIG")
        self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")


        self.rigol.write(":OUTP1 ON");

        self.Camera.arm()




    @kernel
    def after_scan(self):
        delay(100*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()


    def prepare_rigol(self):

        self.rigol = pyvisa.ResourceManager().open_resource('USB0::0x1AB1::0x0641::DG4E232700930::INSTR')
        self.rigol.write(":OUTP1 OFF");
