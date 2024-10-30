# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 16:33:03 2024

@author: E. Porter
"""
from scan_framework import Scan1D, TimeFreqScan
from artiq.experiment import EnvExperiment, BooleanValue, kernel, now_mu, ms, us, MHz,kHz,  NumberValue, delay, parallel, sequential

# imports
import numpy as np
import pyvisa
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel

class Bragg_scanning_exp(Scan1D, TimeFreqScan, EnvExperiment):

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

        self.scan_arguments(times = {'start':0*us,
            'stop':20*us,
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

        self.setattr_argument("dipole_load_time", NumberValue(15.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        self.setattr_argument("drift_time", NumberValue(20.0*1e-3,min=0.0*1e-3,max=100.00*1e-3,scale=1e-3,
               unit="ms"),"parameters")
        self.setattr_argument("field_strength", NumberValue(0.0,min=0.0,max=5.0,scale=1),"parameters")

        self.setattr_argument("phase", NumberValue(119.0,min=0.0,max=359.9,scale=1),"parameters")
        self.setattr_argument("sel_amp", NumberValue(5.5,min=0.0,max=9.9,scale=1),"parameters") # amplitude of locking pulse (scale 0-10V)

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
        self.register_model(self.model, measurement=True, fit=True)


    @kernel
    def before_scan(self):
        self.core.reset()

        self.ttl1.output()
        self.MOTs.init_coils()
        self.MOTs.init_ttls()
        self.MOTs.init_aoms(on=False)
        self.Bragg.init_aoms(on=True)
        self.Bragg.AOMs_off(["Bragg1", "Bragg2"])

        self.MOTs.set_current_dir(0)
        delay(10*ms)
        self.MOTs.dac_0.write_dac(4,self.sel_amp)
        delay(1*ms)


        self.MOTs.take_background_image_exp(self.Camera)
        delay(100*ms)

        self.MOTs.warm_up_MOTs()
        self.core.wait_until_mu(now_mu())

    @kernel
    def measure(self, time, frequency):

        pulse_time = time
        freq = frequency

        self.core.reset()
        delay(1*ms)
        self.core.break_realtime()
        delay(10*ms)
        self.MOTs.dac_0.write_dac(4,self.sel_amp)
        self.MOTs.dac_0.load()
        delay(100*ms)
        self.Bragg.set_AOM_freqs([("Bragg1",99.957*MHz)])

        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)


        self.MOTs.rMOT_pulse()

        # self.MOTs.set_AOM_attens([("Probe",25.0)])
        # self.MOTs.set_AOM_freqs([("Probe",self.MOTs.freq_Probe+400*kHz)])
        # self.MOTs.AOMs_on(["Probe"])
        # delay(10*ms)
        # self.MOTs.AOMs_off(["Probe"])
        # self.MOTs.set_AOM_attens([("Probe",self.MOTs.atten_Probe)])
        # self.MOTs.set_AOM_freqs([("Probe",self.MOTs.freq_Probe)])

        delay(self.dipole_load_time)

        self.Bragg.set_AOM_attens([("Dipole",30.0), ("Homodyne",30.0)])
        self.Bragg.set_AOM_scales([("Dipole",0.6), ("Homodyne",0.1)])
        self.Bragg.AOMs_off(['Homodyne'])

        with parallel:

            self.ttl1.pulse(68*us*1.1) # triggers function gen
            self.Bragg.bragg_pulse(68*us*1.1)


        self.MOTs.dac_0.write_dac(4, 1.5)
        self.MOTs.dac_0.load()
        self.Bragg.set_AOM_freqs([("Bragg1",freq)])
        delay(10*us)

        with parallel:

            self.ttl1.pulse(pulse_time*1.3) # triggers function gen
            self.Bragg.bragg_pulse(pulse_time*1.3)
            delay(500*us)

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

        # return self.Camera.get_push_stats()
        return 0


    def before_measure(self, point, measurement):
        if point > 100:
            point = self.pulse_time

        self.rigol.write(f":SOUR2:FUNC:PULS:PER {str(np.round(3.12*point*1e6,3))}E-6")


        self.Camera.arm()

    @kernel
    def after_scan(self):
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()




    def prepare_rigol(self):
        rm = pyvisa.ResourceManager()
        self.rigol = rm.open_resource('USB0::0x1AB1::0x0643::DG9A241800105::INSTR')
        assert self.rigol.query('*IDN?') =="Rigol Technologies,DG952,DG9A241800105,00.02.06.00.01 \n"

        # turn on and set arb values
        self.rigol.write(f":SOUR2:APPL:USER 100000,1,0.5,{self.phase}")
        self.rigol.write(":SOUR2:FUNC GAUSSPULSE")

        # setup burst parameters
        self.rigol.write(":SOUR2:BURS ON")
        self.rigol.write(":SOUR2:BURS:MODE TRIG")
        self.rigol.write(":SOUR2:BURS:NCYC 1 ")
        self.rigol.write(":SOUR2:BURS:TRIG:SOUR EXT")
        self.rigol.write(":SOUR2:BURS:TDEL 0")
        self.rigol.write(f":SOUR2:BURS:IDLE BOTTOM")


        # turn on output channels
        self.rigol.write(":OUTP2 ON")
