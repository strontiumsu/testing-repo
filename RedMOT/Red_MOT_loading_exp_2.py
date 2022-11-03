# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

@author: sr
"""

import sys
sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")

from artiq.experiment import *
import numpy as np    
from DetectionClass import _Detection
from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689

class Red_MOT_loading_2(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        
        self.setattr_device("core_dma")
        self.setattr_device("zotino0") 
        self.dac=self.get_device("zotino0")
        #self.dac=self.zotino0 
        self.setattr_argument("fdepth1", NumberValue(5,min=0.0,max=7),"rMOT")
        #self.setattr_argument("fdepth2", NumberValue(1,min=0.0,max=7),"rMOT")
        self.setattr_argument("fsingle", NumberValue(0.5,min=0.0,max=7.0),"rMOT")
        self.setattr_argument("fsaw", NumberValue(25*1e3,min=0.0,max=40*1e3,
                      unit="kHz"),"rMOT")
        self.setattr_argument("tbroad",NumberValue(100*1e-3,min=0.0*1e-3,max=200*1e-3,scale = 1e-3,
                      unit="ms"),"rMOT") # Pulse amplitude

        self.setattr_device("ttl7")
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        #self.Zot = ZotinoRamp(self)
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(20.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        # self.setattr_argument("Red_ramp_duration",NumberValue(100.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
        #               unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.0,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(0.0,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(0.0,min=0.0,max=9.00,
                      unit="A"),"MOT coil driver")
       
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Delay_duration",
            Scannable(default=[RangeScan(0.0*1e-3, 500.0*1e-3, 20, randomize=False),NoScan(0.0)],scale=1e-3,
                      unit="ms"),"Loading")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        if not hasattr(self.Delay_duration,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Delay_duration.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
    
        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        #self.Zot.Linear_ramp_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
       
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        #rMOT dac paramters
        self.nsteps = 16
        self.nsaw = round(self.fsaw*self.tbroad)
        self.tdelay = 1/(16*self.fsaw)
        
        self.vbottom1 = self.fdepth1*(0.1/1.4)
        #self.vbottom2 = self.fdepth2*(0.1/1.4)
        self.vsingle = -self.fsingle*(0.1/1.4)
        
        
        #MOTCoildparams
        self.delt = 100*ms/30
        
    @kernel
    def record(self):
        with self.core_dma.record("broad1"):
            for i in range(0,self.nsteps,1):
                delay(self.tdelay*s)
                self.dac.set_dac([-self.vbottom1+self.vbottom1*i/(self.nsteps-1)],[7])
                #if (i == self.nsteps -1):
                #    delay(self.tdelay*s)
                #    self.dac.set_dac([self.vsingle],[7])
            self.dac.set_dac_mu([0],[7])
            
        # with self.core_dma.record("bfield"):
        #     for i in range(30):
        #         delay(self.delt)
        #         self.dac.set_dac([self.Bottom_current_amplitude + (self.Red_current_amplitude-self.Bottom_current_amplitude)/100*ms*i*self.delt],[0])
        #     self.dac.set_dac_mu([0],[0])
            
        # with self.core_dma.record("broad2"):
        #     for i in range(0,self.nsteps,1):
        #         delay(self.tdelay*s)
        #         self.dac.set_dac([-self.vbottom2+self.vbottom2*i/(self.nsteps-1)],[7])
        #         #if (i == self.nsteps -1):
        #         #    delay(self.tdelay*s)
        #         #    self.dac.set_dac([self.vsingle],[7])
        #     self.dac.set_dac_mu([0],[7])
            
        with self.core_dma.record("single"):
            delay(self.tdelay*s)
            self.dac.set_dac([self.vsingle],[7])
            #self.dac.set_dac_mu([0],[7])

        
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        # delay(10*ms)
        # self.ttl5.off() # set red mot light to single frequency
        # delay(10*ms)
        # self.ttl7.on()  # turn off red mot 
        #delay(10*ms)
        
        self.dac.init()
        #timeee = self.core.get_rtio_counter_mu()
        #nowtime = now_mu()
        self.record()
        #print(self.core.mu_to_seconds(self.core.get_rtio_counter_mu() - timeee))
        #print(self.core.mu_to_seconds(now_mu() - nowtime))
        
        
        pulses_handle1 = self.core_dma.get_handle("broad1")
        # pulses_handle2 = self.core_dma.get_handle("broad2")
        pulses_handle3 = self.core_dma.get_handle("single")
        
        #pulses_handleBfield = self.core_dma.get_handle("bfield")
        
        self.core.break_realtime()
        
        Lin_ramp_time = 100*ms

        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        delay(100*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
       
        # Main loop
        for ii in range(len(self.x)):
            self.Detect.arm()
            
            delay(800*ms)
            
            delay(1*ms)
            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
            delay(1*ms)
            
            
            # BACKGROUND IMAGE SEQUENCE
            if self.Background_subtract:
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
                delay(10*ms)
                #self.ttl7.off() #turn on red beam for background image
                #delay(5*ms)
                
                self.Detect.trigger_camera()    # Trigger camera
                #delay(1*ms)
                self.BB.MOT_on() #turn on mot for background image
                delay(self.Detection_pulse_time)
                self.BB.MOT_off()
                
                delay(self.Detect.Exposure_Time)
                self.Detect.acquire()     # Acquire images
                delay(100*ms)
                self.Detect.transfer_background_image(ii)
                delay(300*ms)
            ############################

            #prepare for detection image
            self.Detect.arm()
            delay(300*ms)

            self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading
            delay(1*ms)

            delay(1*ms)
            self.BR.repumpers_on() # turn on repumpers
            delay(1*ms)
            self.MC.Blackman_ramp_up()
            delay(1*ms)
            self.BB.Zeeman_on()
            delay(1*ms)
            self.BB.MOT2D_on() # Turn on atom beam
            delay(1*ms)
            self.BB.MOT_on()
            
            delay(1*ms)
            self.MC.flat()
            
            with parallel:
                self.BB.Zeeman_off()
                self.BB.MOT2D_off() # turn off atom beam
                self.BB.MOT_off() #turn off 3D 
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect) # switch to detection frequency
                ###self.MC.Set_current(self.Bottom_current_amplitude) #ramp down Blue mot coils 
                self.MC.Set_current(self.Red_current_amplitude) #ramp down Blue mot coils 
                self.ttl5.off() #turn on red MOT beam sequence
                self.BR.repumpers_off() # turn off repumpers
            
            #with sequential:
            for i in range(self.nsaw):
                self.core_dma.playback_handle(pulses_handle1)
                    #self.core_dma.playback_handle(pulses_handle3)
            self.core_dma.playback_handle(pulses_handle3)
            delay(self.x[ii])
                # with sequential:
                #     delay(self.Bottom_delay)
                #     #self.BR.repumpers_off() # turn off repumpers
                #     #delay(10*ms)
                #     self.core_dma.playback_handle(pulses_handleBfield)
                    #self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,Lin_ramp_time,30)
            #delay(50*ms)
            
            #delay(self.x[ii])  # Delay
            #delay(1.5*ms)
            # swith 689 to single frequency
            #self.BR.reinit_Red_MOT_aom(20.0, self.BR.Red_MOT_AOM_frequency) # switch to detection frequency
            #delay(self.Red_pulse_duration)
            
            
            #self.BR.Red_MOT_aom_off() # turn off red MOT beam
            self.ttl5.on()
            #self.MC.Set_current(0.0)
            
            #delay(self.x[ii])  # Delay
            
            # IMAGING SEQUENCE
            self.BR.repumpers_on() # turn on repumpers
            self.Detect.trigger_camera()  # Trigger 
            #delay(1*ms)
            
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.repumpers_off() # turn off repumpers
            #self.BB.MOT_off()
            #delay(5*ms)
            ###########################
            self.MC.Set_current(0.0)
            
            self.Detect.acquire()                                # Acquire images
            delay(100*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(100*ms)
            self.Detect.disarm() 
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
            
            
            self.Detect.calc_marginal_stats(ii)
           
           
        delay(500*ms)   
        self.MC.Zero_current()  