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


class _Cooling(EnvExperiment):
    
    def build(self):
        self.setattr_device("core")
        
        ## TTLs      
        self.setattr_device("ttl5") # for turning on and off modulation channel
        self.setattr_device("ttl6") # for switching to single freq channel
        self.setattr_device("ttl3") # MOT coil direction
        self.setattr_device("ttl0") # shutter TTLs
        
        ## AOMS
        
        # RF synth sources
        self.setattr_device('urukul1_cpld')
        
        # names for all our AOMs
        self.AOMs = ["3D", "3P0_repump", "3P2_repump", 'Probe']
        
        # default values for all params for all AOMs
        self.scales = [0.8, 0.8, 0.8, 0.8]     
        self.attens = [6.0, 6.0, 14.0, 6.0] # last two are for nova tech and are scaled between 0 and 1024  
        self.freqs = [90.0, 100.0, 80.0, 200.0] 
   
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
        
        self.setattr_argument("rmot_bb_current",NumberValue(0.25,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")  # broadband mot current
        
        self.setattr_argument("rmot_bb_duration",NumberValue(10.0*1e-3,min=0.0*1e-3,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")  # how long to old broad band 
        
        self.setattr_argument("rmot_ramp_duration",NumberValue(100.0*1e-3,min=0.0,max=200*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")  # how long to ramp between bb and sf
        
        self.setattr_argument("rmot_sf_current",NumberValue(1.25,min=0.0,max=10.0,
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
            NumberValue(1*1e-3,min=0.0*1e-6,max=15000.00*1e-6,scale = 1e-6,
                      unit="us"),"Detection")

        # misc params loaded from datasets
        self.f_MOT3D_load=self.get_dataset('blue_MOT.f_load3D')
        self.f_MOT3D_detect=self.get_dataset('blue_MOT.f_detect')
        self.f_push=self.get_dataset('blue_MOT.f_push')
               
       
    #<><><><><><><>
    # AOM Functions
    #<><><><><><><>
       
    def prepare_aoms(self):
        self.scales = [self.scale_3D, self.scale_3P0_repump, self.scale_3P2_repump, self.scale_Probe]
        self.attens = [self.atten_3D, self.atten_3P0_repump, self.atten_3P2_repump, self.atten_Probe]                     
        self.freqs = [self.freq_3D, self.freq_3P0_repump, self.freq_3P2_repump, self.freq_Probe]
                
        
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
        
            
    @kernel
    def init_ttls(self):
        delay(100*ms)
        self.ttl3.output()
        delay(5*ms)
        self.ttl0.output()
        delay(5*ms)
        self.ttl0.off()
        delay(5*ms)
        self.atom_source = False
        
        
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
            self.ttl0.on()
            self.atom_source = True
    @kernel 
    def atom_source_off(self):
        if self.atom_source:
            self.ttl0.off()
            self.atom_source = False
            
        
    
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
        delay(5*ms)
        self.ttl3.off()
        
       
    @kernel
    def coils_off(self):
        self.dac_0.write_dac(0,0.0)
        self.dac_0.load()
    @kernel
    def molasses_power(self, volt):
        self.dac_0.write_dac(2,volt)
        self.dac_0.load()
    @kernel    
    def set_current(self, cur):
        self.dac_0.write_dac(0,cur)
        self.dac_0.load()

    @kernel
    def set_current_dir(self, direc):
        
        #is this right?
        assert direc in [0,+1]
        self.coils_off()
        delay(6*ms)
        
        if direc == 0:
            delay(5*ms)
            self.ttl3.off()
            delay(5*ms)
        else:
            self.ttl3.on()
        
    @kernel
    def Blackman_ramp_up(self, cur=-1.0):
        if cur ==-1.0: cur = self.bmot_current
        for step in range(0, int((self.Npoints+1)//2)):           
            self.dac_0.write_dac(0, cur*self.window[step])
            self.dac_0.load()
            delay(self.dt)
    
    @kernel
    def Blackman_ramp_down(self):
        for step in range(int((self.Npoints+1)//2), int(self.Npoints)):            
            self.dac_0.write_dac(0, self.bmot_current*self.window[step])
            self.dac_0.load()
            delay(self.dt)
    
    @kernel
    def linear_ramp_down_capture(self, time):
        dt = time/self.Npoints
        for step in range(int(self.Npoints)):            
            self.dac_0.write_dac(0, self.bmot_current+((self.rmot_bb_current-self.bmot_current)/time)*step*dt)
            self.dac_0.load()
            delay(dt)
        
    @kernel
    def linear_ramp(self, bottom, top, time, Npoints):
        dt = time/Npoints
        for step in range(1, int(Npoints)):            
            self.dac_0.write_dac(0, bottom + (top-bottom)/time*step*dt)
            #self.dac_0.write_dac(1,10-5/time*step*dt)
            self.dac_0.load()
            delay(dt)
    @kernel
    def bb_capture_ramps(self, d0, df, ddev0, ddevf, time, Npoints):
        dt = time/Npoints
        self.set_current(self.rmot_bb_current)
        for step in range(1, int(Npoints)):            
            self.dac_0.write_dac(1, 0.143*(d0 + (df-d0)/time*step*dt))
            self.dac_0.write_dac(2, -0.0358*(ddev0 + (ddevf-ddev0)/time*step*dt)+1.2)
            self.dac_0.load()
            delay(dt)
    
    @kernel
    def bb_compression_ramp(self, d0, df, ddev0, ddevf, time, Npoints):
        dt = time/Npoints
        self.set_current(self.rmot_sf_current)
        for step in range(1, int(Npoints)):
            self.dac_0.write_dac(0, self.rmot_bb_current + (self.rmot_sf_current-self.rmot_bb_current)/time*step*dt)            
            self.dac_0.write_dac(1, 0.143*(d0 + (df-d0)/time*step*dt))
            self.dac_0.write_dac(2, -0.0358*(ddev0 + (ddevf-ddev0)/time*step*dt)+1.2)
            self.dac_0.load()
            delay(dt)
            
    @kernel
    def freq_ramp(self, amp, time, Npoints):
        dt = time/Npoints
        for step in range(1, int(Npoints)):            
            self.dac_0.write_dac(2, amp - 2*amp/time*step*dt)
            self.dac_0.load()
            delay(dt)
        self.dac_0.write_dac(2, amp)
        self.dac_0.load()
        
    @kernel
    def cavity_ramp(self, amp, time, Npoints):
        dt = time/Npoints
        for step in range(1, int(Npoints)):            
            self.dac_0.write_dac(3, 8.65 - amp/2 + amp*step*dt/time)
            self.dac_0.load()
            delay(dt)
        self.dac_0.write_dac(3, 8.65)
        self.dac_0.load()
        
    @kernel
    def cavity_scan_trig(self):
        self.dac_0.write_dac(3, 0.0)
        self.dac_0.load()
        delay(1*ms)
        self.dac_0.write_dac(3, 4.0)
        self.dac_0.load()
        delay(4*ms)
        self.dac_0.write_dac(3, 0.0)
        self.dac_0.load()
        
    # this is kinda clunky, fix at some point
    @kernel
    def dac4_switch(self, time):
        self.dac_0.write_dac(4, -1.0)
        self.dac_0.load()
        delay(time)
        self.dac_0.write_dac(4, 0.5)
        self.dac_0.load()
        
    @kernel
    def dac4_switch_opp(self, time):
        self.dac_0.write_dac(4, 0.5)
        self.dac_0.load()
        delay(time)
        self.dac_0.write_dac(4, -1.0)
        self.dac_0.load()
        
    @kernel
    def dac4_low(self):
        self.dac_0.write_dac(4, -1.0)
        self.dac_0.load()
        
    @kernel
    def dac2_set(self, val):
        self.dac_0.write_dac(2, val)
        self.dac_0.load()
        
    @kernel
    def dac_set(self, ch, val):
        self.dac_0.write_dac(ch, val)
        self.dac_0.load()
     
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
        self.set_current_dir(0)
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)

        

        
    @kernel
    def rMOT_pulse(self):
        self.core.break_realtime()
        self.ttl5.on()  # make sure moglabs ch1 off
        self.atom_source_on()        
        self.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.set_current_dir(0)
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)
        
        ### Ramp transfer sequence
        tramp = 100*ms
        dt = tramp/int(self.Npoints)
        for step in range(1, int(self.Npoints)):            
            self.dac_0.write_dac(0, self.bmot_current + 1.0/tramp*step*dt)
            self.dac_0.load()
            self.set_AOM_attens([("3D",6+10*step/int(self.Npoints))])
            delay(dt)
        self.dac_0.write_dac(0, self.bmot_current + 1.0)
        self.dac_0.load()
        #########################################
        
        #with parallel:
        self.atom_source_off()        
        self.AOMs_off(['3D'])
        delay(0.5*us)
        self.set_current(self.rmot_bb_current)
        self.ttl5.off()  # switch on  broadband mode (ch1)
        
        #self.bb_capture_ramps(-3.5, -3, 7, 6, self.rmot_bb_duration, self.Npoints)
            
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
    
    @kernel
    def rMOT_broadband_pulse(self, time):
        self.core.break_realtime()
        self.ttl5.on()  # make sure moglabs ch1 off
        self.ttl6.off()
        self.atom_source_on()        
        self.AOMs_on(["3D", "3P0_repump", "3P2_repump"])
        self.ttl5.off()  # switch on  broadband mode (ch1)
        self.set_current_dir(0)
        self.Blackman_ramp_up()
        self.hold(self.bmot_load_duration)
        
        ### Ramp transfer sequence
        tramp = 100*ms
        dt = tramp/int(self.Npoints)
        for step in range(1, int(self.Npoints)):            
            self.dac_0.write_dac(0, self.bmot_current + 1.0/tramp*step*dt)
            self.dac_0.load()
            self.set_AOM_attens([("3D",6+10*step/int(self.Npoints))])
            delay(dt)
        self.dac_0.write_dac(0, self.bmot_current + 1.0)
        self.dac_0.load()
        #########################################
        
        self.atom_source_off()   
        delay(50*ms)
        self.AOMs_off(['3D'])
        delay(0.5*us)

        self.set_current(self.rmot_bb_current)
        delay(self.rmot_bb_duration)
   
        #self.bb_capture_ramps(-3.5, -3.5, 7, 7, self.rmot_bb_duration, self.Npoints)
        
        # with parallel:
        #     with sequential: 
        #         delay(10*ms)
        #         self.AOMs_off(["3P0_repump","3P2_repump"])
        #     delay(self.rmot_bb_duration)
        #delay(10*ms)
        #self.linear_ramp(self.rmot_bb_current, self.rmot_sf_current, self.rmot_ramp_duration, self.Npoints)
        #self.bb_compression_ramp(-3.5, -3.5, 7,7, self.rmot_ramp_duration, self.Npoints)
        # with parallel:
        #     self.ttl5.on()
        #     self.ttl6.on()
 
        # delay(self.rmot_sf_duration)
        # self.ttl6.off()
        self.set_current(0.0)
    
    @kernel
    def rMOT_beam_pulse(self, dur):
        
        with parallel:
            self.ttl5.on()   # make sure moglabs ch1 off
            self.ttl6.off() # switch RF switch to broadband mode

        self.ttl6.on()
        delay(dur)
        self.ttl6.off()
            
    
    def index_artiq(self, aom) -> TInt32:
        for i in range(len(self.AOMs)):
            if self.AOMs[i] == aom:
                return i
        raise Exception("No AOM with that name")
        
    @kernel
    def take_background_image_exp(self, cam):
        cam.arm()
        delay(2000*ms)
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
                #self.AOMs_on(['3D'])
                #self.AOMs_on(['3P2_repump','3D'])
                self.AOMs_on(['3P0_repump', '3P2_repump', '3D'])
                delay(self.Detection_pulse_time)
                self.AOMs_off(['3D'])
            delay(cam.Exposure_Time)
        self.set_AOM_freqs([('3D', self.freq_3D)])
        self.set_AOM_attens([('3D', self.atten_3D)])



        
    @kernel
    def shelf(self):
        #self.AOMs_on(['688_shelf'])
        delay(0.1*ms)
        #self.AOMs_off(['688_shelf'])
        
        
        
    @kernel
    def push(self):
        #self.ttl1.on()
        #delay(17*ms)
        self.AOMs_on(['Probe'])
        delay(self.Push_pulse_time)
        self.AOMs_off(['Probe'])
        delay(self.Delay_duration)
        #self.AOMs_on(['3P0_repump', '3P2_repump'])
        
        #self.ttl1.off()
    @kernel
    def blow_away(self, time):
        self.atom_source_off()
        self.AOMs_off(['3P0_repump', '3P2_repump', '3D'])
        self.set_AOM_freqs([('3D', self.f_MOT3D_detect)])
        self.set_AOM_attens([('3D', 6.0)])
        self.AOMs_on(['3D'])
        #self.AOMs_on(['3P0_repump','3D'])
        #self.AOMs_on(['3P0_repump', '3P2_repump', '3D'])
        delay(time)
        self.AOMs_off(['3D'])
        self.set_AOM_freqs([('3D', self.freq_3D)])
        self.set_AOM_attens([('3D', self.atten_3D)])
        
        
    @kernel 
    def dipole_power(self, power):
        self.dac_0.write_dac(3, power)
        self.dac_0.load()
        
    @kernel 
    def dipole_AM(self, low, high, time):
        self.dac_0.write_dac(3, low)
        self.dac_0.load()
        delay(time)
        self.dac_0.write_dac(3, high)
        self.dac_0.load()
        delay(time)
        
        