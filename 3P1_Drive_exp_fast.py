# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 16:25:31 2022

@author: sr
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 21:19:34 2022

@author: sr
"""



from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
from Beamline461Class import*
from HCDL import* 


### Procedure ###
# - load blue mot
# - wait time dt
# - obs blue fluorescence wo 689
# - do again with 689

class Drive3P1_fast(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)
        self.BB=Beamline461(self)
        
        self.setattr_argument("Delay_duration", NumberValue(200.0*1e-3,min=0.0*1e-3,max=400.0*1e-3,scale=1e-3,unit='ms'),"Loading")
        self.setattr_argument("Drive689_duration", NumberValue(20.0*1e-3,min=0.0*1e-3,max=400.0*1e-3,scale=1e-3,unit='ms'),"Loading")
        #self.setattr_argument("Background_subtract",BooleanValue(False),"Loading")
        
        
        
        self.setattr_device("urukul2_cpld")
    
        # Probe AOMs
        self.setattr_argument("Drive689_AOM_frequency",
            Scannable(default=[NoScan(84*1e6), RangeScan(80*1e6, 90*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Drive689")

        self.setattr_argument("Drive689_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.9),"Drive689")
        self.setattr_argument("Drive689_Urukul_attenuation",NumberValue(30.0,min=0.0,max=30.0),"Drive689")
        
        if not hasattr(self.Drive689_AOM_frequency,'sequence'):
            self.x=np.array([0,0])
        else:
            self.x=self.Drive689_AOM_frequency.sequence
        self.y=np.full(len(self.x), np.nan) # Prepare result array
        
        
        
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_drive689 = self.get_device("urukul2_ch0")

        
        self.urukul_meas_689 = [self.get_device("urukul2_ch0")]
        
        
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        
        self.drive689_dds_scale=self.Drive689_DDS_amplitude_scale
           
        self.drive689_iatten=self.Drive689_Urukul_attenuation
       
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        
        self.urukul2_cpld.init()


        delay(1*ms)
        self.urukul_hmc_ref_drive689.init()
        self.urukul_hmc_ref_drive689.set_mu(0x40000000, asf=self.urukul_hmc_ref_drive689.amplitude_to_asf(self.drive689_dds_scale))
        self.urukul_hmc_ref_drive689.set_att(self.drive689_iatten)
        self.urukul_hmc_ref_drive689.sw.on()
        
        fdrive689 = self.Drive689_AOM_frequency.sequence
        urukul_ch_689 =self.urukul_meas_689[0]
        
        
        # Prepare datasets
        
        # Camera output datasets
        self.Detect.prep_datasets(self.y)
        self.set_dataset("frequency", self.x, broadcast=True)
        
        for ii in range(len(self.x)):
            
                # fluorescence w 689
                   self.Detect.arm()
                   # Set 689 aom frequency and attenuation 
                   dds_ftw_drive689=self.urukul_meas_689[0].frequency_to_ftw(fdrive689[ii])
            
                   delay(140*ms)
                   urukul_ch_689.init()
                   urukul_ch_689.set_mu(dds_ftw_drive689, asf=urukul_ch_689.amplitude_to_asf(self.drive689_dds_scale))
                   urukul_ch_689.set_att(self.drive689_iatten)

                   delay(50*ms)
                       
                   self.BB.shift_MOT2D_aom_frequency(25.0)                  # Shift 2D MOT frequency
                   delay(1*ms)
                   self.BB.set_MOT3DDP_aom_frequency(self.BB.f_MOT3D_load)  # Set 3D MOT frequency for loading   
                   delay(130*ms)
                   
                   # if self.Background_subtract:
                   #      self.Detect.trigger_camera()    # Trigger camera 
                   #      delay(self.Detect.Exposure_Time)
                   #      self.Detect.acquire()     # Acquire images
                   #      self.Detect.transfer_background_image(ii)
                   # delay(200*ms)
                   self.MC.Blackman_ramp_up()
                   
                   urukul_ch_689.sw.on()  # turn on 689 drive
                   self.MC.flat()
                   self.BB.shift_MOT2D_aom_frequency(0.0)                  # Turn on atom beam
                   
                   #delay(self.Delay_duration)                                     # Delay duration 
                   #self.Detect.arm()
                   
                   delay(self.Drive689_duration)
                   with parallel:
                       self.BB.set_MOT3DDP_aom_frequency(self.BB.f_MOT3D_detect)  # Set 3D MOT frequency for detection
                       self.Detect.trigger_camera()                               # Trigger camera
                       
                   delay(self.Detect.Exposure_Time)
                   self.MC.Blackman_ramp_down()
                   delay(130*ms)
                   self.Detect.acquire()                                # Acquire images
                   self.Detect.transfer_image(ii)
                                     # Disarm camera   
                          
                   #self.Detect.print_bg_image_array()
                   #self.Detect.print_image_array()
                   #self.Detect.print_bg_subtracted_image_array()
                   # Shift 2D MOT frequency back to loading frequency
                   
                   self.Detect.disarm() 
                   delay(70*ms)
                   urukul_ch_689.sw.off()  # turn on 689 drive
                   self.mutate_dataset("frequency",ii,self.x[ii])
                   self.mutate_dataset("detection.index",ii,ii)
                   
             
        
        delay(100*ms)   
        self.MC.Zero_current()  
        
            #self.Detect.clean_up()