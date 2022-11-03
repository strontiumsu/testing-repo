# -*- coding: utf-8 -*-
"""
Created on Tue Sep 20 10:49:32 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 13:26:48 2022

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
from ThreePhoton689Class import _ThreePhoton689 
from artiq.coredevice.ad9910 import PHASE_MODE_TRACKING

class Three_photon_Rabi_flopping_vphase(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl5")
        self.setattr_device("ttl6")
        self.setattr_device("ttl7")
        self.Detect=_Detection(self)
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        self.th_ph=_ThreePhoton689(self)
        
        
    
        #self.Zot = ZotinoRamp(self)
        
        # MOTdriver parameters
        self.setattr_argument("Red_pulse_duration",NumberValue(200.0*1e-3,min=0.0*1e-3,max=300.0*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Bottom_current_amplitude",NumberValue(0.0,min=0.0,max=5.00,
                      unit="A"),"MOT coil driver")
        
        self.setattr_argument("Bottom_delay",NumberValue(0.0,min=0.0,max=100*1e-3,scale = 1e-3,
                      unit="ms"),"MOT coil driver")
        
        self.setattr_argument("Red_current_amplitude",NumberValue(0.0,min=0.0,max=9.00,
                      unit="A"),"MOT coil driver")
       
        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        self.setattr_argument("Push_pulse_time",NumberValue(1.0*1e-6,min=0.0*1e-6,max=500.00*1e-3,scale = 1e-9,
                      unit="ns"),"Detection")
        
        self.setattr_argument("Delay_duration",
            NumberValue(5,min=0.0*1e-6,max=15000.00*1e-6,scale = 1e-6,
                      unit="us"),"Detection")
        
        self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
            
        
        self.setattr_argument("Rabi_t_pulse",
            Scannable(default=[RangeScan(0.0*1e-6, 5.0*1e-6, 20, randomize=False),NoScan(0.0)],scale=1e-6,
                      unit="us"),"Floppin")
        
        self.setattr_argument("Rabi_pulse_freq",
            Scannable(default=[RangeScan(60.0*1e+6, 80.0*1e+6, 20, randomize=False),NoScan(85.0*1e6)],scale=1e+6,
                      unit="MHz"),"Floppin")


        self.tscan = False
        self.fscan=False
        self.x=[]
        
        if (hasattr(self.Rabi_pulse_freq,'sequence')):
            self.t0=self.Rabi_t_pulse.value
            self.ph0=self.Rabi_pulse_phase.value
            self.x=self.Rabi_pulse_freq.sequence
            self.f0=self.x[0]
            self.fscan=True
            
        elif (hasattr(self.Rabi_t_pulse,'sequence')):
            self.f0=self.Rabi_pulse_freq.value
            self.ph0=self.Rabi_pulse_phase.value
            self.x=self.Rabi_t_pulse.sequence
            self.t0=self.x[0]
            self.tscan=True
            

        # else:
        #    print('PICK ONE VARIABLE TO SCAN!')
           
        self.y=np.full(len(self.x), np.nan) # Prepare result array
    
        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        #self.Zot.Linear_ramp_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
        self.th_ph.set_atten()
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()

        
    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        self.th_ph.set_phase_mode(PHASE_MODE_TRACKING)
        
        
        #self.th_ph.init_aoms()
        
        self.th_ph.set_switch1_689_3nu_freq(self.f0)
        
        Lin_ramp_time = 100*ms
        self.ttl7.off()
        
        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("time_delay", self.x, broadcast=True)
        
        delay(10*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        self.BB.Probe_AOM_off()
        delay(1*ms)
        self.BR.Hp688_aom_off()
        # delay(1*ms)
        # self.th_ph.switch1_off()
        # delay(1*ms)
        # self.th_ph.switch2_off()
        # delay(1*ms)
        # self.th_ph.switch3_off()
       
        # Main loop
        for ii in range(len(self.x)):
            self.Detect.arm()
            delay(175*ms)

            self.BB.MOT2D_off()  # turn off 2D MOT beam
            delay(1*ms)
            self.BB.Zeeman_off()
            delay(1*ms)
            
            if self.tscan:
                tdelay = self.x[ii]
                freqshift = self.f0
            elif self.fscan:
                tdelay = self.t0
                freqshift = self.x[ii]
            
            t=now_mu() # Determine reference time for phase tracking
            self.th_ph.init_aoms_phase(t) # Initialize aoms with phase considered
            # Set scannable variable
            if self.fscan:
                self.th_ph.set_switch1_phase_freq(freqshift,0.0,t)
                #self.th_ph.set_switch1_689_3nu_freq(self.x[ii])

            # BACKGROUND IMAGE SEQUENCE
            if self.Background_subtract:
                self.BB.reinit_MOT3DDP_aom(6.0, self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for imaging
                delay(10*ms)
                self.BR.repumpers_on() # turn on repumpers
                self.Detect.trigger_camera()    # Trigger camera
                self.BB.MOT_on() #turn on mot for background image
                delay(self.Detection_pulse_time)
                self.BB.MOT_off()
                delay(self.Detect.Exposure_Time)
                self.BR.repumpers_off() # turn off repumpers
                self.Detect.acquire()     # Acquire images
                delay(50*ms)
                self.Detect.transfer_background_image(ii)
                delay(50*ms)
             
            ############################

            #prepare for detection image
            self.Detect.arm()
            delay(175*ms)

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
                self.MC.Set_current(self.Bottom_current_amplitude) #ramp down Blue mot coils  
                self.ttl5.off()
            

            delay(self.Bottom_delay)
            self.BR.repumpers_off() # turn off repumpers
            self.MC.Linear_ramp(self.Bottom_current_amplitude,self.Red_current_amplitude,Lin_ramp_time,30)

            with parallel:
                self.ttl5.on() #turn off modulation channel
                self.ttl6.on() #switch to single-frequency channel
            delay(self.Red_pulse_duration) #single frequency stage time
            self.ttl6.off() #switch back to mod channel (which is off)

            self.MC.Set_current(0.0)
            self.ttl7.on() # trigger quantiation B field pulse

            with parallel:
                with sequential:
                    delay(1498.75*us)
                    if self.tscan:
                        delay(self.x[ii])
                    else:
                        delay(self.t0)
                    with parallel:
                        self.BR.repumpers_on() # turn on repumpers
                        self.BB.Probe_AOM_on()
                        self.BR.Hp688_aom_on()
                    
                with sequential:
                    delay(1500*us)
                    self.th_ph.switch1_on()
                    if self.tscan:
                        delay(self.x[ii])
                    else:
                        delay(self.t0)
                    self.th_ph.switch1_off()

                with sequential:
                    delay(1500*us)
                    self.th_ph.switch2_on()
                    if self.tscan:
                        delay(self.x[ii])
                    else:
                        delay(self.t0)
                    self.th_ph.switch2_off()
                    
                with sequential:
                    delay(1500*us)
                    self.th_ph.switch3_on()
                    if self.tscan:
                        delay(self.x[ii])
                    else:
                        delay(self.t0)
                    self.th_ph.switch3_off()

            delay(self.Push_pulse_time)#+0.75*us)
            
            with parallel:
                self.BR.repumpers_off() # turn off repumpers
                self.BB.Probe_AOM_off()
                self.BR.Hp688_aom_off()
            
            self.ttl7.off() #resef B field pulse
            delay(self.Delay_duration)
            
            # IMAGING SEQUENCE
            self.BR.repumpers_on() # turn on repumpers
            self.Detect.trigger_camera()  # Trigger 
            self.BB.MOT_on()
            delay(self.Detection_pulse_time)
            self.BB.MOT_off()
            delay(self.Detect.Exposure_Time)
            self.BR.repumpers_off() # turn off repumpers
            ###########################
           
            
            self.Detect.acquire()                                # Acquire images
            delay(50*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            delay(50*ms)
             
          
            self.mutate_dataset("time_delay",ii,self.x[ii])
            self.mutate_dataset("detection.index",ii,ii)
            
            
            self.Detect.calc_push_stats(ii)
           
           
        delay(500*ms)   
        self.MC.Zero_current()  
        
    