# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 19:37:10 2022

@author: sr
"""


from artiq.experiment import *
import numpy as np    
from Detection import *
from MOTcoils import* 
import scipy.optimize
# from CurveFitClass import* 


class Blue_MOT_opt(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.Detect=Detection(self)
        self.MC=MOTcoils(self)

        self.setattr_device("ttl4")
        self.setattr_device("urukul1_cpld")

        ## Read in data sets
        self.f_MOT3D_load=self.get_dataset('blue_MOT.f_load3D')
        self.f_MOT3D_detect=self.get_dataset('blue_MOT.f_detect')
        self.f_MOT2D=self.get_dataset('blue_MOT.f_load2D')
        self.f_Zeeman=self.get_dataset('blue_MOT.f_loadZeeman')
    
        
        # 3D MOT AOM  
        self.setattr_argument("MOT3DDP_AOM_frequency",
            Scannable(default=[RangeScan(self.f_MOT3D_load-5*1e6, self.f_MOT3D_load+5*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT3DDP")

        self.setattr_argument("MOT3DDP_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT3DDP")
                      
        self.setattr_argument("MOT3DDP_Urukul_attenuation",NumberValue(self.get_dataset('blue_MOT.attenuation3D'),min=1.0,max=30.0),"MOT3DDP")
        
        # Detection w 3D MOT
        self.setattr_argument("Detection_frequency",
            Scannable(default=[RangeScan(self.f_MOT3D_detect-5*1e6, self.f_MOT3D_detect+5*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT3DDP")
        
        # Zeeman slower AOM
        self.setattr_argument("Zeeman_AOM_frequency",
            Scannable(default=[RangeScan(self.f_Zeeman-1*1e6, self.f_Zeeman+1*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"Zeeman")

        self.setattr_argument("Zeeman_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.95),"Zeeman")
        self.setattr_argument("Zeeman_Urukul_attenuation",NumberValue(self.get_dataset('blue_MOT.attenuationZeeman'),min=0.0,max=30.0),"Zeeman")

        # 2D MOT AOM
        self.setattr_argument("MOT2D_AOM_frequency",
            Scannable(default=[RangeScan(self.f_MOT2D-5*1e6, self.f_MOT2D+5*1e6, 10, randomize=False)],scale=1e6,
                      unit="MHz"),"MOT2D")

        self.setattr_argument("MOT2D_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT2D")
        self.setattr_argument("MOT2D_Urukul_attenuation",NumberValue(self.get_dataset('blue_MOT.attenuation2D'),min=1.0,max=30.0),"MOT2D")
        
        # Optimization option
        self.setattr_argument("Optimization_option",NumberValue(0,min=0,max=4),"User Options")
        self.setattr_argument("Background_subtract",BooleanValue(False),"User Options")

        self.setattr_argument("MOT2D_DDS_amplitude_scale",NumberValue(0.8,min=0.0,max=0.8),"MOT2D")
        self.setattr_argument("MOT2D_Urukul_attenuation",NumberValue(self.get_dataset('blue_MOT.attenuation2D'),min=1.0,max=30.0),"MOT2D")

        self.setattr_argument("Detection_pulse_time",NumberValue(1.0*1e-3,min=0.0,max=10.00*1e-3,scale = 1e-3,
                      unit="ms"),"Detection")
        
        # Urukul clock output syntonized to the RTIO clock.
        # Can be used as HMC830 reference on Sayma RTM.
        # When using this reference, Sayma must be recalibrated every time Urukul
        # is rebooted, as Urukul is not synchronized to the Kasli.
        self.urukul_hmc_ref_MOT2D = self.get_device("urukul1_ch0")
        self.urukul_hmc_ref_MOT3DDP = self.get_device("urukul1_ch1")
        self.urukul_hmc_ref_Zeeman = self.get_device("urukul1_ch2")

        
        self.urukul_meas = [self.get_device("urukul1_ch0"),self.get_device("urukul1_ch1"),self.get_device("urukul1_ch2")]
        
        self.fixed_vars = [self.f_Zeeman,self.f_MOT2D,self.f_MOT3D_load,self.f_MOT3D_detect]
        
        self.scanning_var = []


        # if hasattr(self.Detection_frequency,'sequence') and not hasattr(self.BB.MOT3DDP_AOM_frequency,'sequence'):
        #     self.x=self.Detection_frequency.sequence
        #     self.f_detect=self.x[0]
        #     self.f_MOT=self.BB.MOT3DDP_AOM_frequency.value
        #     self.f_detect_scan=True
        #     self.f_MOT_scan=False
        # elif not hasattr(self.Detection_frequency,'sequence') and hasattr(self.BB.MOT3DDP_AOM_frequency,'sequence'):  
            
        #     self.x=self.BB.MOT3DDP_AOM_frequency.sequence
        #     self.f_MOT=self.x[0]
        #     self.f_detect=self.Detection_frequency.value
        #     self.f_detect_scan=False
        #     self.f_MOT_scan=True
        # else: 
        #     print('PICK ONLY ONE VARIABLE TO SCAN!')
    
    def prepare(self):  
        
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        #self.BB.set_atten()
        # Initialize camera
        self.Detect.camera_init()
        self.Detect.disarm()
        
        self.Zeeman_dds_scale=self.Zeeman_DDS_amplitude_scale
        self.MOT2D_dds_scale=self.MOT2D_DDS_amplitude_scale
        self.MOT3DDP_dds_scale=self.MOT3DDP_DDS_amplitude_scale
        #self.probeDP_dds_scale=self.ProbeDP_DDS_amplitude_scale
           
        self.Zeeman_iatten=self.Zeeman_Urukul_attenuation
        self.MOT2D_iatten=self.MOT2D_Urukul_attenuation
        self.MOT3DDP_iatten=self.MOT3DDP_Urukul_attenuation
        
        self.scan_vars = [self.Zeeman_AOM_frequency.sequence,
                          self.MOT2D_AOM_frequency.sequence,
                          self.MOT3DDP_AOM_frequency.sequence,
                          self.Detection_frequency.sequence]
        
        self.user_opt = self.Optimization_option
        
        
    
    @kernel    
    def run(self):
        
        self.core.reset()
        self.MC.init_DAC()   # Initialize MOT coil DAC
        
        delay(1*ms)
        self.urukul1_cpld.init()

        self.urukul_hmc_ref_MOT3DDP.init()
        self.urukul_hmc_ref_MOT3DDP.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT3DDP.amplitude_to_asf(self.MOT3DDP_dds_scale))
        self.urukul_hmc_ref_MOT3DDP.set_att(self.MOT3DDP_iatten)
        self.urukul_hmc_ref_MOT3DDP.sw.on()
            
            
        self.urukul_hmc_ref_Zeeman.init()
        self.urukul_hmc_ref_Zeeman.set_mu(0x40000000, asf=self.urukul_hmc_ref_Zeeman.amplitude_to_asf(self.Zeeman_dds_scale))
        self.urukul_hmc_ref_Zeeman.set_att(self.Zeeman_iatten)
        self.urukul_hmc_ref_Zeeman.sw.on()

            
        self.urukul_hmc_ref_MOT2D.init()
        self.urukul_hmc_ref_MOT2D.set_mu(0x40000000, asf=self.urukul_hmc_ref_MOT2D.amplitude_to_asf(self.MOT2D_dds_scale))
        self.urukul_hmc_ref_MOT2D.set_att(self.MOT2D_iatten)
        self.urukul_hmc_ref_MOT2D.sw.on()


        delay(5*ms)
        #for i in range(len(self.scan_vars)):
        #for i in range(1):
        i = int(self.user_opt)
            
        delay(50*ms)

        self.scanning_var = self.scan_vars[i]

        runfMOT3Dload=self.f_MOT3D_load
        runfMOT3Ddetect = self.f_MOT3D_detect
        runfMOT2D = self.f_MOT2D
        runfZeeman = self.f_Zeeman
            
        delay(50*ms)
            
            
        urukul_ch =self.urukul_meas[2]
        urukul_ch.init()
        dds_ftw_Zeeman=self.urukul_meas[2].frequency_to_ftw(self.f_Zeeman)
        urukul_ch.set_mu(dds_ftw_Zeeman, asf=urukul_ch.amplitude_to_asf(self.Zeeman_dds_scale))
        urukul_ch.set_att(self.Zeeman_iatten)
        urukul_ch.sw.on()
                                
                    
        urukul_ch =self.urukul_meas[0]
        urukul_ch.init()
        dds_ftw_MOT2D=self.urukul_meas[0].frequency_to_ftw(self.f_MOT2D)
        urukul_ch.set_mu(dds_ftw_MOT2D, asf=urukul_ch.amplitude_to_asf(self.MOT2D_dds_scale))
        urukul_ch.set_att(self.MOT2D_iatten)
        urukul_ch.sw.on() 
                
           
        urukul_ch =self.urukul_meas[1]
        urukul_ch.init()
        dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(self.f_MOT3D_load)
        urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))
        urukul_ch.set_att(self.MOT3DDP_iatten)
        urukul_ch.sw.on()
            
        delay(50*ms)

        self.Detect.prep_datasets(self.scanning_var)
            
        delay(500*ms)
        
        print(self.scanning_var)

        #Main loop
        for ii in range(len(self.scanning_var)):
                
            if i == 0:
                runfZeeman = self.scanning_var[ii]
                delay(2*ms)
                urukul_ch =self.urukul_meas[2]
                dds_ftw_Zeeman=self.urukul_meas[2].frequency_to_ftw(runfZeeman)
                urukul_ch.set_mu(dds_ftw_Zeeman, asf=urukul_ch.amplitude_to_asf(self.Zeeman_dds_scale))
                            
                
            elif i == 1:
                runfMOT2D = self.scanning_var[ii]
                delay(2*ms)
                urukul_ch =self.urukul_meas[0]
                dds_ftw_MOT2D=self.urukul_meas[0].frequency_to_ftw(runfMOT2D)
                urukul_ch.set_mu(dds_ftw_MOT2D, asf=urukul_ch.amplitude_to_asf(self.MOT2D_dds_scale))
                
            elif i == 2:
                runfMOT3Dload = self.scanning_var[ii]
                delay(2*ms)
                urukul_ch =self.urukul_meas[1]
                dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(runfMOT3Dload)
                urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))
                    
            elif i == 3:
                runfMOT3Ddetect = self.scanning_var[ii]
                    
            self.set_dataset("frequency", self.scanning_var, broadcast=True)
            delay(300*ms)
                
            self.Detect.arm()
           
            delay(300*ms)
          
           
            if self.Background_subtract:
                urukul_ch =self.urukul_meas[1]
                dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(runfMOT3Ddetect)
                urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))  # Set 3D MOT frequency for loading   
                urukul_ch.sw.off()
                delay(200*ms)
                self.Detect.trigger_camera()    # Trigger camera 
                urukul_ch.sw.on()
                delay(self.Detection_pulse_time)
                urukul_ch.sw.off()
                delay(self.Detect.Exposure_Time)
                self.Detect.acquire()     # Acquire images
                self.Detect.transfer_background_image(ii)
                delay(300*ms)

            urukul_ch =self.urukul_meas[1]
            dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(runfMOT3Dload)
            urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))  # Set 3D MOT frequency for loading   
            delay(200*ms)
                
            self.MC.Blackman_ramp_up()
            
            urukul_ch.sw.on()
            self.MC.flat()                                   # Delay duration 
            self.Detect.arm()
            with parallel:
                with sequential:
                    urukul_ch =self.urukul_meas[1]
                    urukul_ch.sw.off()
                    dds_ftw_MOT3DDP=self.urukul_meas[1].frequency_to_ftw(runfMOT3Ddetect)
                    urukul_ch.set_mu(dds_ftw_MOT3DDP, asf=urukul_ch.amplitude_to_asf(self.MOT3DDP_dds_scale))# Set 3D MOT frequency for detection
            self.Detect.trigger_camera() # Trigger camera
            urukul_ch.sw.on()
            delay(self.Detection_pulse_time)
            urukul_ch.sw.off()
               
            delay(self.Detect.Exposure_Time)
            delay(5*ms)
            self.MC.Blackman_ramp_down()
                
                
            delay(200*ms)
            self.Detect.acquire()
            delay(20*ms)
            self.Detect.transfer_image_background_subtracted(ii)
            #self.Detect.transfer_image(ii)
            delay(200*ms)
            self.Detect.disarm() 
                
          
            delay(50*ms)
            self.mutate_dataset("frequency",ii,self.scanning_var[ii])
            self.mutate_dataset("detection.index",ii,ii)
            
            self.Detect.calc_marginal_stats(ii)
                
        ## Analyze data and update datasets
        ## Find frequency with maximum florescence and set data set to that value
        
       
        
        delay(100*ms)   
        self.MC.Zero_current() 
        
#    def analyze(self):
        
        
        # self.Fit = CurveFit(self)
        
        # self.Fit.parabolaFit(self.get_dataset('frequency'),self.get_dataset('detection.background_subtracted_image_sum'))