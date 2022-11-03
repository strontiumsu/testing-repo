"""
Created on Thu Aug 11 14:23:42 2022

@author: sr
"""
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.append("C:/Users/sr/Documents/Artiq/artiq-master/repository/Classes")


from artiq.experiment import EnvExperiment, Scannable, RangeScan, NoScan, NumberValue, kernel, ms, delay, parallel
   

from MOTCoilsClass import _MOTCoils
from Beamline461Class import _Beamline461
from Beamline689Class import _Beamline689



class Blue_MOT_atom_count(EnvExperiment):
    
    def build(self): 
        self.setattr_device("core")
        self.setattr_device("ttl4")
        self.MC=_MOTCoils(self)
        self.BB=_Beamline461(self)
        self.BR=_Beamline689(self)
        self.setattr_device("sampler0")
        self.adc_0=self.get_device("sampler0")
        self.adc_data=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0];
        
        start_det, stop_det, points_det = 10*1e6, 50*1e6, 5
        start_pow, stop_pow, points_pow = 1, 10, 10
        
        # standard settings
        
        
         # which detunings to sweep through
        self.setattr_argument("Mot_frequency", Scannable(default=[RangeScan(90*1e6, 
                     100*1e6,5, randomize=False), NoScan(97*1e6)], scale=1e6),"PD")
         # which powers to sweep through
        self.setattr_argument("Mot_attenuation",
            Scannable(default=[RangeScan(6.0,30.0,5, randomize=False),NoScan(6.0)],scale=1,
                      unit="dBm"),"PD")

        self.setattr_argument("PD_delay",NumberValue(1*1e-3,min=0.0,max=1000.00*1e-3,scale = 1e-3,
                      unit="ms"),"PD")
        self.setattr_argument("samples",NumberValue(10,min=1.0,max=100,scale = 1),"PD")


 
      
    def prepare(self):  
       
        # Prepare MOT pulse shape
        self.MC.Blackman_pulse_profile()
        # Set AOM attenuations
        self.BB.set_atten()
        self.BR.set_atten()
        
        self.dets = self.Mot_frequency.sequence
        self.attens = self.Mot_attenuation.sequence
       

    @kernel    
    def run(self):
        
        # general inicialization
        self.core.reset()
        self.MC.init_DAC()
        self.BB.init_aoms()
        self.BR.init_aoms()
        
        self.adc_0.init()
        
        shots = len(self.dets)*len(self.attens)
        self.set_dataset('V_std', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V_std_zero', [0 for _ in range(shots)], broadcast = True)
        self.set_dataset('V_zero', [0 for _ in range(shots)], broadcast = True)
        
        # self.set_dataset('P_std', np.zeros(shots), broadcast = True)
        # self.set_dataset('P', np.zeros(shots), broadcast = True)
        
        
        delay(100*ms)
        self.BB.MOT2D_off()  # turn off 2D MOT beam
        delay(1*ms)
        self.BB.Zeeman_off()
        delay(1*ms)
        self.BB.Probe_AOM_off()
        self.BR.Hp688_aom_off()
        delay(1*ms)
        delay(5000*ms)
       
        # Main loop
        jj = 0
        for det in self.dets:
            for atten in self.attens:
                """
                Pulse sequence has five steps
                A: Set stanfard params, measures PD voltage with MOT
                B: Switch to (det, pow), measure PD voltage with MOT
                C: Turn off everything, allow atoms to clear
                D: Turn on beams to (det, pow), but no atoms, measure PD voltage
                E: turn on beams to standard params, but no atoms, measure PD voltage
                """
                
                
                self.BB.reinit_MOT3DDP_aom(atten, det)
                delay(5000*ms)
                #A
                # self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)
                # delay(1*ms)
                # self.BR.repumpers_on()
                # delay(1*ms)
                # self.MC.Blackman_ramp_up()
                # delay(1*ms)
                # self.BB.Zeeman_on()
                # delay(1*ms)
                # self.BB.MOT2D_on()
                # delay(1*ms)
                # self.BB.MOT_on()
                
                # delay(0.2*ms)
                # self.ttl4.on()
                # delay(0.2*ms)
                # self.ttl4.off()
                # #allow to equilibrate
                # delay(1000*ms) 
                
                # self.mutate_dataset("V_std", jj, self.sample_ADC())
                # delay(5*ms)
                
                # # B
                # # Change settings
                # self.BB.reinit_MOT3DDP_aom(atten, det)
                # self.mutate_dataset("V", jj, self.sample_ADC())
                # delay(5*ms)
                
                
                # # C
                # self.BB.Zeeman_off()
                # self.BB.MOT2D_off() # turn off atom beam
                # self.BB.MOT_off() #turn off 3D 
                # self.MC.Set_current(0.0) #ramp down Blue mot coils 
                # delay(1000*ms)

                
                # # D
                # # Change settings
                # self.BB.MOT_on()
                # self.mutate_dataset("V_zero", jj, self.sample_ADC())
                # delay(5*ms)
                
                # # E
                # # Back to standard settings
                # self.BB.reinit_MOT3DDP_aom(self.BB.MOT3DDP_iatten, self.BB.f_MOT3D_load)
                # self.mutate_dataset("V_std_zero", jj, self.sample_ADC())
                # delay(5*ms)

                # # turn off
                # self.BB.Zeeman_off()
                # self.BB.MOT2D_off() # turn off atom beam
                # self.BB.MOT_off() #turn off 3D 
                # self.MC.Set_current(0.0) #ramp down Blue mot coils 
                # jj += 1
        
        
      
        delay(200*ms)   
        self.MC.Zero_current()  
    @kernel 
    def sample_ADC(self):
        res = 0.
        CHANNELS = 8
        dat=[0.1 for _ in range(CHANNELS)]
        for jj in range(int(self.samples)):
            self.adc_0.sample(dat)
            res += float(dat[0])
            delay(self.PD_delay)
        return res/self.samples
    
    
    
    # def analyze(self):
    #     power = 1
    #     P_std = power*np.ones((len(self.dets), len(self.powers))) 
    #     P = power*np.ones((len(self.dets), len(self.powers))) 
    #     V_std = np.array(self.get_dataset("V_std")).reshape((len(self.dets), len(self.powers)))
    #     V_std_zero = np.array(self.get_dataset("V_std_zero")).reshape((len(self.dets), len(self.powers)))
    #     V = np.array(self.get_dataset("V")).reshape((len(self.dets), len(self.powers)))
    #     V_zero = np.array(self.get_dataset("V")).reshape((len(self.dets), len(self.powers)))
    #     G = P/P_std*(V_std-V_std_zero)/(V-V_zero)
        
    #     fig, ax = plt.subplots()
    #     shapes = ['.' 'x', 'v', 's', 'o']
    #     colors = ['r', 'b', 'g', 'o', 'p']
    #     for i in len(G):
    #         ax.plot(self.powers, G[i], s=shapes[i], color=colors[i], label = str(self.dets[i]))
    #     ax.set_xlabel('Power (units?)')
    #     ax.set_ylabel('G')
    #     ax.set_title("G vs. power for atom counting")
    #     plt.legend()
    #     plt.show()
            
            
        