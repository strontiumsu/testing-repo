# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 16:33:03 2024

@author: G. panelli
"""
from scan_framework import Scan1D, TimeFreqScan
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Experiments/Classes")
from artiq.experiment import EnvExperiment, BooleanValue, kernel, now_mu, ms, us, MHz,kHz,  NumberValue, delay, parallel, sequential

# imports
import numpy as np
import pyvisa
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel

class Bragg_Scan_Vsel_exp(Scan1D, TimeFreqScan, EnvExperiment):

    def build(self, **kwargs):
    # required initializations

        super().build(**kwargs)
        self.setattr_device("ttl1")

        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)
        self.rigol= None
        self.ind = 0

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
        self.setattr_argument("pulse_shape",BooleanValue(True),"parameters")


        self.setattr_argument("amplitude", NumberValue(5.0,min=0.0,max=9.9,scale=1,
               unit="V", ndecimals = 3),"parameters")
        self.setattr_argument("phase", NumberValue(122.0,min=0.0,max=359.9,scale=1),"parameters")

        self.setattr_argument("v_select",BooleanValue(True),"parameters")
        self.setattr_argument("sel_amp", NumberValue(5.5,min=0.0,max=9.9,scale=1),"parameters")
        self.setattr_argument("blow_wait_duration", NumberValue(5*1e-3,min=0.0,max=300*1e-3,scale=1e-3,
               unit="ms", ndecimals = 3),"parameters")
        self.setattr_argument("sequential",BooleanValue(False),"parameters")

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


        self.MOTs.take_background_image_exp(self.Camera)
        delay(100*ms)

        self.MOTs.atom_source_on()
        self.MOTs.AOMs_on(['3D', "3P0_repump", "3P2_repump", "Probe"])
        delay(2000*ms)
        self.MOTs.AOMs_off(['3D', "3P0_repump", "3P2_repump", "Probe"])
        self.MOTs.atom_source_off()

    @kernel
    def measure(self, time, frequency):

        pulse_time = time
        freq = frequency
        self.core.wait_until_mu(now_mu())
        self.core.reset()
        delay(100*ms)
        self.Camera.arm()
        delay(400*ms)

        self.MOTs.dac_0.write_dac(4, self.sel_amp) #set bragg pulse amplitude
        self.MOTs.dac_0.load()


        self.MOTs.AOMs_off(self.MOTs.AOMs)
        delay(15*ms)
        self.MOTs.rMOT_pulse()

        delay(self.dipole_load_time)


        self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
        self.Bragg.set_AOM_scales([("Dipole",0.6 ), ("Homodyne",0.2)])
        self.Bragg.AOMs_off(['Homodyne'])

        #Blow away pulse ####################################################################################
        if self.v_select:
            with parallel:
                self.Bragg.AOMs_on(['Bragg1', "Bragg2"])
                self.ttl1.on()

            delay(pulse_time) # updates the true pulse time due to discretization errors

            with parallel:
                self.Bragg.AOMs_off(['Bragg1', "Bragg2"])
                self.ttl1.off()

            self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",30.0)])

            #Blow away pulse ##########################################################################
            delay(self.blow_wait_duration)
            self.MOTs.AOMs_on(['Probe'])# turn probe beam on
            self.MOTs.dac_0.write_dac(3, 5.0) #trigger scan
            self.MOTs.dac_0.load()
            delay(1*ms)
            self.MOTs.AOMs_off(['Probe']) #turn off probe beam
            self.MOTs.dac_0.write_dac(3, 0.0)
            self.MOTs.dac_0.load()

        # Pulse preparation ##############################################################################
        with parallel:
            with sequential:
                self.MOTs.dac_0.write_dac(4, self.amplitude) #set bragg pulse amplitude
                self.MOTs.dac_0.load()
                delay(5*us)
            #compensate for Doppler shift
            self.Bragg.set_AOM_freqs([('Bragg2',freq)]) # adjust for Doppler


        ### second pulse #################################################################################
        if self.sequential:
            self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
            self.Bragg.set_AOM_scales([("Dipole",0.6 ), ("Homodyne",0.1)])
            self.Bragg.AOMs_off(['Homodyne'])
            ##############
            with parallel:
                self.Bragg.AOMs_on(['Bragg1', "Bragg2"])
                self.ttl1.on()

            delay(pulse_time) # updates the true pulse time due to discretization errors

            with parallel:
                self.Bragg.AOMs_off(['Bragg1', "Bragg2"])
                self.ttl1.off()



        self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",30.0)])


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

        return self.Camera.get_push_stats()


    def before_measure(self, point, measurement):
        if point > 100:
            point = self.pulse_time

        self.rigol.write(f":SOUR1:FUNC:PULS:PER {str(np.round(3.12*point*1e6,3))}E-6")
        self.rigol.write(":SYST:CSC CH1,CH2")

    @kernel
    def after_scan(self):
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        self.MOTs.atom_source_on()

    def prepare_rigol(self):
        rm = pyvisa.ResourceManager()
        self.rigol = rm.open_resource('USB0::0x1AB1::0x0643::DG9A241800105::INSTR')
        assert self.rigol.query('*IDN?') =="Rigol Technologies,DG952,DG9A241800105,00.02.06.00.01 \n"

        # turn on and set arb values
        self.rigol.write(f":SOUR1:APPL:USER 100000,{self.amplitude},{self.amplitude/2},{self.phase}")
        self.rigol.write(":SOUR1:FUNC GAUSSPULSE")

        # setup burst parameters
        self.rigol.write(":SOUR1:BURS ON")
        self.rigol.write(":SOUR1:BURS:MODE TRIG")
        self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")
        self.rigol.write(":SOUR1:BURS:TDEL 0")
        idle = "BOTTOM" if self.pulse_shape else "TOP"
        self.rigol.write(f":SOUR1:BURS:IDLE {idle}")
        self.rigol.write(":SYST:CSC CH1,CH2")

        # turn on output channels
        self.rigol.write(":OUTP1 ON")
        self.rigol.write(":OUTP2 ON")
