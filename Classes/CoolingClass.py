# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 18:16:29 2023

@author: sr

Desc: This file contains the class that controls all blue MOT methods (loading, ect.)
"""

from artiq.experiment import RTIOUnderflow, EnvExperiment, NumberValue, delay, ms, sequential, kernel, TInt32, parallel, us
import numpy as np

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")
from NovaTechClass import _NovaTech


class _Cooling(EnvExperiment):
    
    def build(self):
        self.setattr_device("core")
        
        ## TTLs      
        self.setattr_device("ttl5") # for turning on and off modulation channel
        self.setattr_device("ttl6") # for switching to single freq channel
        self.setattr_device("ttl3") # MOT coil direction
        self.setattr_device("ttl0") # Zeeman and 2D MOT
        
        ## AOMS
        
        self.nova = _NovaTech(self)
        
        # RF synth sources
        self.setattr_device('urukul1_cpld')
        
        self.nova = _NovaTech(self)
        self.setattr_device("ttl0")
        
        # names for all our AOMs
        self.AOMs = ["3D", "3P0_repump", "3P2_repump", '813']
        # self.AOMs = ['Zeeman', '2D', "3D", "Probe", "3P0_repump", "3P2_repump", '688_shelf']
        self.nova_AOMs = ['Zeeman', '2D']
        
        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8, 500, 500]     
        self.attens = [6.0, 6.0, 9.0, 6.0] # last two are for nova tech and are scaled between 0 and 1024  
        self.freqs = [90.0, 100.0, 100.0, 100.0, 195.0, 210.0 ] 
   
        self.urukul_channels = [self.get_device("urukul1_ch0"),
                                self.get_device("urukul1_ch1"),
                                self.get_device("urukul1_ch2"),
                                self.get_device("urukul1_ch3")]
        
        # setting attributes to controll all AOMs       
        for i in range(len(self.AOMs)):
            AOM = self.AOMs[i]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=0.9), f"{AOM}_AOMs")
            self.setattr_argument(f"atten_{AOM}", NumberValue(self.attens[i], min=1.0, max=30), f"{AOM}_AOMs")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")
        
        for j in range(len(self.nova_AOMs)):
            i = j + len(self.AOMs)
            AOM = self.nova_AOMs[j]
            self.setattr_argument(f"scale_{AOM}", NumberValue(self.scales[i], min=0.0, max=1024.0), f"{AOM}_AOMs")
            self.setattr_argument(f"freq_{AOM}", NumberValue(self.freqs[i]*1e6, min=50*1e6, max=350*1e6, scale=1e6, unit='MHz'),  f"{AOM}_AOMs")
        
        
        self.atom_source = False # flag to keep track of whether or not 2D and zeeman are on
        
        
        ## MOT Coils
        self.setattr_device("zotino0")
        self.dac_0=self.get_device("zotino0")
        
        
        self.setattr_argument("bmot_ramp_duration",NumberValue(50.0*1e-3,min=1.0*1e-3,max=100.00*1e-3,scale=1e-3,
                      unit="ms"),"MOT coil driver") # ramp duration
        
        self.setattr_argument("bmot_current",NumberValue(5.0,min=0.0,max=10.0,
                      unit="A"),"MOT coil driver") # Pulse amplitude
        
        self.setattr_argument("bmot_load_duration", NumberValue(1000.0*1e-3,min=10.0*1e-3,max=9000.00*1e-3,scale=1e-3,
                      unit="ms"),"MOT coil driver") # how long to hold blue mot on to load atoms
        
        self.setattr_argument("rmot_bb_current",NumberValue(0.15,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")  # broadband mot current
        
        self.setattr_argument("rmot_bb_duration",NumberValue(10.0*1e-3,min=4.0*1e-3,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")  # how long to old broad band 
        
        self.setattr_argument("rmot_ramp_duration",NumberValue(100.0*1e-3,min=0.0,max=200*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")  # how long to ramp between bb and sf
        
        self.setattr_argument("rmot_sf_current",NumberValue(1.15,min=0.0,max=10.0,
                      unit="A"),"MOT coil driver") # single frequency mot current
        
        self.setattr_argument("rmot_sf_duration",NumberValue(25.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")  # how long to hold atoms in sf red mot
               
        self.setattr_argument("Npoints",NumberValue(30,min=0,max=100.00),"MOT coil driver")
        
        
        ## Misc params
        self.setattr_argument("Push_pulse_time",NumberValue(2.5*1e-6,min=0.0*1e6,max=50000.00*1e-3,scale = 1e-6,
                      unit="us"),"Detection")
        self.setattr_argument("Detection_pulse_time",NumberValue(0.2*1e-3,min=0.0,max=100.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        self.setattr_argument("Delay_duration",
            NumberValue(3*1e-3,min=0.0*1e-6,max=15000.00*1e-6,scale = 1e-6,
                      unit="us"),"Detection")

        # misc params loaded from datasets
        self.f_MOT3D_load=self.get_dataset('blue_MOT.f_load3D')
        self.f_MOT3D_detect=self.get_dataset('blue_MOT.f_detect')
        self.f_push=self.get_dataset('blue_MOT.f_push')
               
       
    #<><><><><><><>
    # AOM Functions
    #<><><><><><><>
       
    def prepare_aoms(self):
        self.scales = [self.scale_3D, self.scale_3P0_repump, self.scale_3P2_repump, self.scale_813]
        
        self.attens = [self.atten_3D, self.atten_3P0_repump, self.atten_3P2_repump, self.atten_813]
                       
        self.freqs = [self.freq_3D, self.freq_3P0_repump, self.freq_3P2_repump, self.freq_813]
        
        
        self.nova.table_init()
        ind = 0
        for _ in range(5):
            self.nova.table_write(ind, 0, 0, 0, 0)
            self.nova.table_write(ind+1, self.freq_Zeeman/2, self.scale_Zeeman/2, self.freq_2D, self.scale_2D)
            ind += 2
        self.nova.table_start()
        
    @kernel
    def init_aoms(self, on=False):
   
        delay(10*ms)
        self.urukul1_cpld.init()

        for i in range(len(self.AOMs)):
            delay(10*ms)
           
            ch =  self.urukul_channels[i]
            
            ch.init()            
            set_f = ch.frequency_to_ftw(self.freqs[i])
            set_asf = ch.amplitude_to_asf(self.scales[i])
            ch.set_mu(set_f, asf=set_asf)
            ch.set_att(self.attens[i])
            if on:
                ch.sw.on()
            else:                
                ch.sw.off()
        delay(10*ms)
        
        
        # add in initializing novatech here
            
    @kernel
    def init_ttls(self):
        delay(100*ms)
        self.ttl3.output()
        self.ttl0.output()
        self.ttl0.on()
        
        
    # basic AOM methods
    @kernel
    def AOMs_on(self, AOMs):
        with parallel:
            for aom in AOMs:
                self.urukul_channels[self.index_artiq(aom)].sw.on()

    @kernel
    def AOMs_off(self, AOMs):
        with parallel:
            for aom in AOMs:
                self.urukul_channels[self.index_artiq(aom)].sw.off()

    @kernel        
    def set_AOM_freqs(self, freq_list): # takes in a list of tuples
        with parallel:
            for aom, freq in freq_list:
                ind = self.index_artiq(aom)
                self.freqs[ind] = freq
                ch = self.urukul_channels[ind]
                set_freq = ch.frequency_to_ftw(freq)
                set_asf = ch.amplitude_to_asf(self.scales[ind])
                ch.set_mu(set_freq, asf=set_asf)
    
    
    
    @kernel        
    def set_AOM_attens(self, atten_list):
        with parallel:
            for aom, atten in atten_list:
                ind  = self.index_artiq(aom)
                self.attens[ind] = atten
                self.urukul_channels[ind].set_att(atten)

    @kernel        
    def set_AOM_scales(self, scale_list):
        with parallel:
            for aom, scale in scale_list.items():
                ind = self.index_artiq(aom)
                self.scales[ind] = scale
                ch = self.urukul_channels[ind]
                set_freq = ch.frequency_to_ftw(self.freqs[ind])
                set_asf = ch.amplitude_to_asf(self.scales[ind])
                ch.set_mu(set_freq, asf=set_asf)

    @kernel 
    def atom_source_on(self):
        if not self.atom_source:
            delay(-80*us)
            self.ttl0.off()
            delay(5*us)
            self.ttl0.on()
            self.atom_source = True
            delay(75*us)
    @kernel 
    def atom_source_off(self):
        if self.atom_source:
            delay(-80*us)
            self.ttl0.off()
            delay(5*us)
            self.ttl0.on()
            self.atom_source = False
            delay(75*us)
        
    
    #<><><><><><><><>
    # Coil Functions
    #<><><><><><><><>
    
    def prepare_coils(self):
        self.Npoints += (1-self.Npoints%2)
        self.window = np.blackman(self.Npoints)  
        self.dt = self.bmot_ramp_duration/((self.Npoints-1)//2)
        
    
    @kernel
    def init_coils(self):
        self.dac_0.init()
        self.ttl3.off()
       
    @kernel
    def coils_off(self):
        self.dac_0.write_dac(0,0.0)
        self.dac_0.load()
    
    @kernel    
    def set_current(self, cur):
        self.dac_0.write_dac(0,cur)
        self.dac_0.load()

    @kernel
    def set_current_dir(self, direc):
        assert direc in [0,+1]
        if direc == 1:
            self.ttl3.off()
        else:
            self.ttl3.on()
        
    @kernel
    def Blackman_ramp_up(self):
        for step in range(0, int((self.Npoints+1)//2)):           
            self.dac_0.write_dac(0, self.bmot_current*self.window[step])
            self.dac_0.load()
            delay(self.dt)
    
    @kernel
    def Blackman_ramp_down(self):
        for step in range(int((self.Npoints+1)//2), int(self.Npoints)):            
            self.dac_0.write_dac(0, self.bmot_current*self.window[step])
            self.dac_0.load()
            delay(self.dt)
        
    @kernel
    def linear_ramp(self, bottom, top, time, Npoints):
        dt = time/Npoints
        for step in range(1, int(Npoints)):            
            self.dac_0.write_dac(0, bottom + (top-bottom)/time*step*dt)
            self.dac_0.load()
            delay(dt)
            
    @kernel 
    def hold(self, time):
        delay(time)

    
    #<><><><><><><><><><><>
    # General MOT Functions
    #<><><><><><><><><><><>
    
    @kernel
    def bMOT_pulse(self):
        self.atom_source_on()        
        self.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)
        self.Blackman_ramp_down()
        self.AOMs_off(["3D", "3P0_repump", "3P2_repump"])
        self.atom_source_off()
    
    @kernel
    def bMOT_load(self):
        self.atom_source_on()        
        self.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)

        

        
    @kernel
    def rMOT_pulse(self):
        self.core.break_realtime()
        self.ttl5.on()  # make sure moglabs ch1 off
        self.atom_source_on()        
        self.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)
        
        
        with parallel:
            self.atom_source_off()        
            self.AOMs_off(['3D'])
            self.set_current(self.rmot_bb_current)
            self.ttl5.off()  # switch on  broadband mode (ch1)
            
        delay(self.rmot_bb_duration)
        
        with parallel:
            self.AOMs_off(["3P0_repump","3P2_repump"])
            self.linear_ramp(self.rmot_bb_current, self.rmot_sf_current, self.rmot_ramp_duration, self.Npoints)
            
        with parallel:
            self.ttl5.on()
            self.ttl6.on()
            
        delay(self.rmot_sf_duration)
        
        self.ttl6.off()
        self.set_current(0.0)
    
    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")
        
    @kernel
    def take_background_image_exp(self, cam):
        cam.arm()
        delay(500*ms)
        self.take_MOT_image(cam)
        delay(200*ms)
        cam.process_background()
        
    @kernel
    def take_MOT_image(self, cam):
        self.atom_source_off()
        self.AOMs_off(['3P0_repump', '3P2_repump', '3D'])
        self.set_AOM_freqs([('3D', self.f_MOT3D_detect)])
        self.set_AOM_attens([('3D', 6.0)])
        with parallel:
            cam.trigger_camera()
            with sequential:
                self.AOMs_on(['3P0_repump', '3P2_repump', '3D'])
                delay(self.Detection_pulse_time)
                self.AOMs_off(['3D'])
            delay(cam.Exposure_Time)
        self.set_AOM_freqs([('3D', self.freq_3D)])
        self.set_AOM_attens([('3D', self.atten_3D)])



        
    # @kernel
    # def shelf(self):
    #     self.AOMs_on(['688_shelf'])
    #     delay(0.1*ms)
    #     self.AOMs_off(['688_shelf'])
        
        
        
    # @kernel
    # def push(self):
    #     self.AOMs_on(['Probe'])
    #     delay(self.Push_pulse_time)
    #     self.AOMs_off(['Probe'])
    #     self.AOMs_on(['3P0_repump', '3P2_repump'])
    #     delay(self.Delay_duration)
        
        