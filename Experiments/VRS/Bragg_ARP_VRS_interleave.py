# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 16:11:41 2024

@author: ejporter
"""


from scan_framework import Scan1D, TimeFreqScan
from artiq.coredevice import ad9910
import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
# imports
import numpy as np
import pyvisa
from CoolingClass import _Cooling
from CameraClass import _Camera
from BraggClass import _Bragg
from repository.models.scan_models import RabiModel


class Bragg_ARP_VRS__interleave_exp(Scan1D, TimeFreqScan, EnvExperiment):
    
    
    def build(self, **kwargs):
        
        super().build(**kwargs)
        self.setattr_device("ttl1") # triggering pulse
        
        # import classes for experiment control
        self.MOTs = _Cooling(self)
        self.Camera = _Camera(self)
        self.Bragg = _Bragg(self)
        self.scan_dds = self.Bragg.urukul_channels[1] # easy access to channel 1 for scan
        
        self.rigol= None
        
        # attributes here
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
            frequency_center={'default':100.000*MHz},
            pulse_time= {'default':0*us},
            nbins = {'default':1000},
            nrepeats = {'default':1},
            npasses = {'default':1},
            fit_options = {'default': "No Fits"}
        
            )
    
        self.setattr_argument("dipole_load_time", NumberValue(15.0*1e-3,min=0.0*1e-3,max=1000.00*1e-3,scale=1e-3,
                      unit="ms"),"parameters")
        
        self.setattr_argument("amplitude", NumberValue(0.8,min=0.0,max=1.2,scale=1,
               unit="V", ndecimals = 3),"parameters")
        self.setattr_argument("phase", NumberValue(0.0,min=0.0,max=359.9,scale=1),"parameters")
        self.setattr_argument("n", NumberValue(1,min=0,max=20,scale=1),"parameters")
        
        self.freq_list= np.linspace(100.0*MHz, 100.0*MHz, 1024)
        self.freq_list_ram = np.full(1024, 1)
        self.step_size=0
        
        self.setattr_argument(f"freq_range", NumberValue(100*1e3, min=0*1e3, max=50000*1e3, scale=1e3, unit='kHz'),  "parameters")
        self.setattr_argument(f"offset", NumberValue(0*1e3, min=0*1e3, max=1000*1e3, scale=1e3, unit='kHz'),  "parameters")
        
        
    
        
        
    def prepare(self):
            #prepare/initialize mot hardware and camera
        self.prepare_rigol()
        self.MOTs.prepare_aoms()
        self.MOTs.prepare_coils()
        self.Camera.camera_init()
        self.Bragg.prepare_aoms()
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
        delay(50*ms)
        
        # set cavity scan triger to zero
        self.MOTs.dac_0.write_dac(3, 0.0)
        self.MOTs.dac_0.load()
        delay(5*ms)
        
        self.MOTs.warm_up_MOTs()
        self.core.wait_until_mu(now_mu())
        
    
    def before_measure(self, point, measurement):
        if point > 100: # this means were doing frequency scan
            f = point
            t = self.pulse_time
        else:    #doing time scan   
            f = self.frequency_center
            t = point
        
        
        t = int(t/(1024*4*1e-9))*(1024*4*1e-9) # update with discretization error
        
        self.rigol.write(f":SOUR1:APPL:SEQ {int(8192/t)}")
        self.rigol.write(f":SOUR1:BURS:IDLE 33700")
        self.rigol.write(":SYST:CSC CH1,CH2")
        
        self.Camera.arm()

        
    
    @kernel
    def prepare_freq_ramp(self, t, f):
        self.step_size = int(t/(1024*4*ns))  
        f0 = f+self.freq_range/2 ## note we have to count backwards, thats how it reads out
        f_step = self.freq_range/1023
        
        for i in range(1024):            
            self.freq_list[i] = f0-f_step*i
        self.scan_dds.frequency_to_ram(self.freq_list, self.freq_list_ram)
        
        
        self.core.break_realtime()
        delay(10 * ms)
        self.scan_dds.set(f-self.freq_range/2, amplitude=self.Bragg.scale_Bragg1)
        delay(1 * ms)
        
        
        
        self.scan_dds.set_cfr1(ram_enable=0)     
        self.scan_dds.cpld.io_update.pulse_mu(8)
        
        self.scan_dds.set_profile_ram(start=0, end=1024-1, step=(self.step_size | (2**6 - 1 ) << 16),
                                  profile=0, mode=ad9910.RAM_MODE_RAMPUP)
        self.scan_dds.cpld.set_profile(0)
        
        delay(100*us) # needs 2x delays here not to throw RTIOUnderflow Error?????
        delay(100*us)

        self.scan_dds.cpld.io_update.pulse_mu(8)
        delay(100*us)
        self.scan_dds.write_ram(self.freq_list_ram)
        # prepare to enable ram and set frequency as target
        delay(10 * us)
        self.scan_dds.set_cfr1(internal_profile=0, ram_enable=1, ram_destination=ad9910.RAM_DEST_FTW)
        delay(10*ms)
        
        self.core.wait_until_mu(now_mu())

    @kernel
    def measure(self, time, freq):
    
        pulse_time = time
        freq = freq
        
        for n in range(3):
            freq = self.frequency_center+6*(n-1)*4*10.68
        
            self.core.reset()
            delay(1 * ms)
            delay(100*ms)
            self.Camera.arm()
            delay(400*ms)
            
            self.prepare_freq_ramp(pulse_time, freq)
            delay(1 * ms)        
            
            pulse_time = self.step_size*(1024*4*ns) # updates the true pulse time due to discretization errors
            delay(1 * ms)
            
            # before this point is just for preparing the RAM and RIGOL
            self.core.break_realtime()
            delay(100*ms)
            self.MOTs.AOMs_off(self.MOTs.AOMs)
            delay(50*ms)
            self.MOTs.AOMs_off(['Probe']) #turn off probe beam
            delay(50*ms)
            self.MOTs.rMOT_pulse()
            delay(self.dipole_load_time)
            
            self.Bragg.set_AOM_attens([("Dipole",30.0 ), ("Homodyne",30.0)])
            self.Bragg.set_AOM_scales([("Dipole",0.6 ), ("Homodyne",0.1)])
            self.Bragg.AOMs_off(['Homodyne'])
            
            if n != 1:
                with parallel:
                    self.scan_dds.cpld.io_update.pulse_mu(8)
                    self.Bragg.AOMs_on(['Bragg1', "Bragg2"])
                    self.ttl1.on()
                delay(pulse_time)
                with parallel:
                    self.Bragg.AOMs_off(['Bragg1', "Bragg2"])
                    self.ttl1.off()
            else:
                delay(pulse_time)
            
            delay(10*us)
            # Scan the cavity probe
            self.MOTs.AOMs_on(['Probe'])# turn probe beam on
            self.MOTs.dac_0.write_dac(3, 5.0) #trigger scan
            self.MOTs.dac_0.load()
              
            
            self.scan_dds.set_cfr1(ram_enable=0)
            self.scan_dds.cpld.io_update.pulse_mu(8)
        
            
            
            with parallel:
                delay(0*ms)
                with sequential:
                    self.scan_dds.set_cfr1(ram_enable=0)
                    self.scan_dds.cpld.io_update.pulse_mu(8)
                with sequential:
                    delay(1*ms)
                    self.MOTs.AOMs_off(['Probe']) #turn off probe beam
            
            self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",30.0)])
            self.MOTs.take_MOT_image(self.Camera)
            self.Bragg.set_AOM_attens([("Dipole",self.Bragg.atten_Dipole ), ("Homodyne",self.Bragg.atten_Homodyne)])
            self.Bragg.set_AOM_scales([("Dipole",self.Bragg.scale_Dipole ), ("Homodyne",self.Bragg.scale_Homodyne)])
            self.Bragg.AOMs_on(['Homodyne'])
            
            #reset Cavity scan trigger to 0
            delay(5*ms)
            self.MOTs.dac_0.write_dac(3, 0.0)
            self.MOTs.dac_0.load()
    
            delay(50*ms)
            self.Camera.process_image(bg_sub=True)
            delay(400*ms)
            self.core.wait_until_mu(now_mu())
            delay(200*ms)
            self.MOTs.AOMs_off(['3P0_repump', '3P2_repump', '3D', "Probe"])
            delay(200*ms)
            
            
            self.core.wait_until_mu(now_mu()) 
        self.core.wait_until_mu(now_mu()) 
        return 0
    
    @kernel
    def after_scan(self):
        self.core.break_realtime()
        self.core.wait_until_mu(now_mu())
        delay(100*ms)
        self.MOTs.AOMs_on(self.MOTs.AOMs)
        delay(10*ms)
        self.MOTs.atom_source_on()
    
    def prepare_rigol(self):
        rm = pyvisa.ResourceManager()
        self.rigol = rm.open_resource('USB0::0x1AB1::0x0643::DG9A241800105::INSTR') 
        assert self.rigol.query('*IDN?') =="Rigol Technologies,DG952,DG9A241800105,00.02.06.00.01 \n"
    
        self.rigol.write(f":SOUR1:APPL:SEQ 27000000,{self.amplitude},{self.amplitude/2},{self.phase}")
        
        
        # setup burst parameters
        self.rigol.write(":SOUR1:BURS ON")
        self.rigol.write(":SOUR1:BURS:MODE TRIG")
        self.rigol.write(":SOUR1:BURS:NCYC 1 ")
        self.rigol.write(":SOUR1:BURS:TRIG:SOUR EXT")
        self.rigol.write(":SOUR1:BURS:TDEL 0")
        self.rigol.write(f":SOUR1:BURS:IDLE 33700")
        self.rigol.write(":SYST:CSC CH1,CH2")
        
        # turn on output channels
        self.rigol.write(":OUTP1 ON")
        self.rigol.write(":OUTP2 ON")
    