"""
A single qubit experiment is a readout resonator coupled to a qubit.

We use the General_QM_Exps and OPXexp() classes in order to do experiments
on this system
Done: 
    * start_qm --> start_qm_octave    -- Done 
    * Create a more general run experiment function with the following attributes:
        * A dictionary that controls our inputs to experiments and outputs - Done
        * A manifest of all experiments we can run - Done (note, did it in a simpler way with the eval finction)
    * Implement rabi experiment. - Done
    * Move dbm function out, might just be worth inputting in volts - Done (note, removed volt functionality)
    * Implement h5py file for output - Done
    
    * Implement experiments - Done
        *Ramsey
        *T1
    * Fix gaussian waveform - Done
    
To Do:
    * Create a new folder for the calibration json file
    * Slab h5py implementation
    * move all material properties of OPX, ie, LO frequency, IF frequency into OPX config, ie, keep things outside of init. 
    * Come up with a scheme for calibration
    * Create a pseudo device config that allows us to specify our parameters
    * Fix sub 16 ns pulses and their structure in the code
*** Ask Quantum Machines people the following ***

* Efficiency of the mixers that we use
"""

from qm.QuantumMachinesManager import QuantumMachinesManager
from qm.octave import *
from qm.octave.octave_manager import ClockMode
from qm.qua import *
import os
import time
import matplotlib.pyplot as plt
from qualang_tools.units import unit
import config as config
import h5py
import numpy as np
from slab.instruments import InstrumentManager
from OPXexperiments import OPXexp
from General_QM_Experiments import General_QM_Exps

from oldConfig import config as initialConfiguration 
import json


opx_ip = "192.168.88.252"
opx_port = 9510
octave_ip = "192.168.88.254"
octave_port = 80
con = "con1"
octave = "octave1"
with open("experiments.json", "r") as f:
    experiment_config = json.load(f)

class Single_Qubit_Experiments(General_QM_Exps, OPXexp):
    """
    Starting with a preexisting configuration file with various experiments, we change our qubit frequencies in order to actually

    
    """
    
    def __init__(self, initConfig = initialConfiguration):
        """OPX configuration"""

        super().__init__({}, initConfig)
        self.elements = list(self.OPX_config['elements'].keys())
        """Setup complete, now we can run octave programs"""
        
    
 
    """
    Creates our quantum machine using an octave config and other values.
    Launch just before you begin a job; but after you have altered all of
    your OPX_config parameters

    """
 

    def start_QM_octave(self, calibrationFile = os.getcwd()):
        
        self.octave_config = QmOctaveConfig()
        # set up calibration database for octave (calibration_db.json)
        self.octave_config.set_calibration_db(calibrationFile)
        self.octave_config.add_device_info(octave, octave_ip, octave_port)
        ###Create Octave mapping, see introduction.py for more info ###
        self.octave_config.set_opx_octave_mapping([(con, octave)])

        ###Creating quantum machine ####
        self.qmm = QuantumMachinesManager(host=opx_ip, port=opx_port, octave=self.octave_config)
        # self.reloadOPXConfig()
        
        self.qm = self.qmm.open_qm(self.OPX_config)
        
        ###If we want to calibrate elements beforehand we can specify###
        # if calibration:
        #     for el in elements:
        #         print("-" * 37 + f" Calibrates {el}")
        #         self.qm.octave.calibrate_element(el, [(LO, IF)])  # can provide many pairs of LO & IFs.
        #         self.qm = self.qmm.open_qm(self.OPX_config)

        ###Assuming we are using the internal octave clock###=
        self.qm.octave.set_clock(octave, clock_mode=ClockMode.Internal)
        ###Setting the LO Source we're using (the internal octave source) ###
        for el in self.elements:
            if('mixInputs' in list(self.OPX_config['elements'][el].keys())):
                self.qm.octave.set_lo_source(el, OctaveLOSource.Internal)  # Use the internal synthetizer to generate the LO.
                self.qm.octave.set_rf_output_gain(el, 0)  # can set the gain from -10dB to 20dB
                self.qm.octave.set_rf_output_mode(el, RFOutputMode.trig_normal)  # set the behaviour of the RF switch to be 'on'.
                                                                                # set the behaviour of the RF switch to be on only when triggered
                                                                                # 'RFOutputMode' can be : on, off, trig_normal or trig_inverse
        
        ###Sets the downconversion from the octave to RF2in and assigns it to the resonator element###
        self.qm.octave.set_qua_element_octave_rf_in_port('resonator', octave, 2)
        ###Sets the downconverter and its LO Source to the internal downconverter in the octave ###
        self.qm.octave.set_downconversion(
            'resonator', lo_source=RFInputLOSource.Internal, if_mode_i=IFMode.direct, if_mode_q=IFMode.direct
        )
        ###Sets the downconversion from the octave to RF1in and assigns it to the qubit element###
        self.qm.octave.set_qua_element_octave_rf_in_port('qubit', octave, 1)
        ###Sets the downconverter and its LO Source to the internal downconverter in the octave ###
        self.qm.octave.set_downconversion(
            'qubit', lo_source=RFInputLOSource.Internal, if_mode_i=IFMode.direct, if_mode_q=IFMode.direct
        )

        ### Loads calibration data from calibration_db.json (note: to calibrate need to add more mixer calibrations, need to run calibrate function within this class)###
        for element in self.elements:
            if("mixInputs" in self.OPX_config['elements'][element]): 
                self.qm.octave.calibrate_element(element, {}, close_open_quantum_machines=True)
        self.reloadOPXConfig()

        # if(calibration):
        #     self.paramFile = paramFile
        #     with open(paramFile, 'r') as f:
        #         param_config = json.load(f)
        #     paramList = []
        #     for element in param_config:
        #         LOFrequencies = param_config[element]["LOFrequencies"]
        #         IFFrequencies = param_config[element]["IFFrequencies"]
                
        #         """HARDWARE LIMITED TEMPORARY MEASURE 1: We only can support 1 LO frequency and 1 IF frequency at this moment
        #             due to an update that needs to be done on the OPX. In the meanwhile, the below function
        #             is used; implementation for multiple freqs is present but is inefficient
        #             in system at moment. We only use the middle value of paramList to account for this
        #         """
        #         for i in range(len(LOFrequencies)):
        #             paramList= [(float(LOFrequencies[i]), float(IFFrequencies[i]))]
        #             self.qm.octave.calibrate_element(element, paramList, close_open_quantum_machines=True)
        #         self.qm = self.qmm.open_qm(self.OPX_config)
                
        #         # paramList = [paramList[int(len(paramList)/2)]]
        #         # self.qm.octave.calibrate_element(element, paramList, close_open_quantum_machines=True)
                

       
        return None
    """
    Requirement: have run start_QM_Octave()
    
    Allows you to refresh the OPX config so that any edits do not require
    you to create a new config file.
    """

    def reloadOPXConfig(self, opxConfig = None):
        if(opxConfig is None):
            opxConfig = self.OPX_config
        self.OPX_config = opxConfig

        self.qm = self.qmm.open_qm(self.OPX_config)
        
        return self.OPX_config


    """
    We have a calibration dictionary called calibration_params.json that we store the parameters for the qubit and resonator calibration.

    It takes the following form:
        {
            "qubit": {
                "LOFrequencies": [
                    5000000000.0
                ],
                "IFFrequencies": []
            },
            "resonator": {
                "LOFrequencies": [],
                "IFFrequencies": []
            }
        }
        The class below allows us to edit the "LOFrequencies" and "IFFrequencies" dictionary
        
        We take an element which must be either "qubit" or "resonator"

        We then pass in a paramFile which is a string that specifies the name and location of the file

        We pass in LOFrequencies which is a list of LOFrequencies we wish to test for
        
        We pass in IFFrequencies which is a list of IFFrequencies we wish to test for

        Note that IFFrequencies and LOFrequencies must be the same length: in the actual calibration step
        we will make one to one in order maps from LOFrequencies to IFFrequencies that will lead to pairs of (LO, IF):
            LOFreq = [LO1, LO2, LO3, ...]
            IFFreq = {IF1, IF2, IF3, ...}

            ListOfLOIFs = [(LO1, IF1), (LO2, IF2), (LO3, IF3)]
    """
    def editCalibrationParams(self,  element, paramFile = "calibration_params.json", LOFrequencies = None, IFFrequencies = None):
        if(not (element == "qubit" or element == "resonator")):
            raise Exception("Element not valid, please choose qubit or resonator")

        with open(paramFile, "r") as f:
            param_config = json.load(f)
        
        if(LOFrequencies is not None):
            if(len(IFFrequencies)!=len(LOFrequencies)):
                raise Exception("IFFrequency length is not equivalent to LOFrequency length")

            param_config[element]["LOFrequencies"] = LOFrequencies
        
        if(IFFrequencies is not None):
            if(len(IFFrequencies)!=len(LOFrequencies)):
                raise Exception("IFFrequency length is not equivalent to LOFrequency length")

            param_config[element]["IFFrequencies"] = IFFrequencies
        
        if(len(param_config[element]["LOFrequencies"])!=len(param_config[element]["IFFrequencies"])):
            raise Exception("IFFrequency length is not equivalent to LOFrequency length")

        with open(paramFile, "w") as f:
            json.dump(param_config, f)
         
        return param_config
    """
    Requirement: Have run start_QM_Octave()

    HARDWARE: Connect RF1 to RF1in and RF2 to RF2in

    Allows you to calibrate individual elements
    
    From the paramFile (which is set to a default but can be changed) we extract LOFrequencies and IFFrequencies.
    From here we will make one to one in order maps from LOFrequencies to IFFrequencies that will lead to pairs of (LO, IF):
            LOFreq = [LO1, LO2, LO3, ...]
            IFFreq = [IF1, IF2, IF3, ...]

            paramList = [(LO1, IF1), (LO2, IF2), (LO3, IF3)]
    
    We can then pass this to the calibrate_element function 

    Calibrating requires you to have already started the octave with the start_QM_octave function. 

    
    """
    def calibrate(self, paramFile = "calibration_params.json"):

        self.paramFile = paramFile
        
        with open(paramFile, 'r') as f:
            param_config = json.load(f)
        
        paramList = []
        
        for element in param_config:
            LOFrequencies = param_config[element]["LOFrequencies"]
            IFFrequencies = param_config[element]["IFFrequencies"]
            
            """HARDWARE LIMITED TEMPORARY MEASURE 1: We only can support 1 LO frequency and 1 IF frequency at this moment
                due to an update that needs to be done on the OPX. In the meanwhile, the below function
                is used; implementation for multiple freqs is present but is inefficient
                in system at moment. We only use the middle value of paramList to account for this
            """
            for i in range(len(LOFrequencies)):
                paramList= [(float(LOFrequencies[i]), float(IFFrequencies[i]))]
                self.qm.octave.calibrate_element(element, paramList, close_open_quantum_machines=True)
            self.reloadOPXConfig()

    """
    This function allows you to run any experiment and get a dictionary of results.
    Takes: 
        *experiment_name: type = string, description: name of the experiment we 
         seek to run, constraints: must be within the experiments.json and 
         implemented_experiments (see OPXexperiments.py and experiments.json)
        *calibration: type: bool, description: Choose whether or not you 
         would like to calibrate the octave before running experiment
        *gain: type = float, description: value from -10db to 20 dB that defines
         the gain from rf output, constraints: ensure that any output is within
         the limits of the octave and the qubit you are running
        *dc_current: type = float, description: value in amps that defines a current
        sent into the system from an external yokogawa gs200 current source. Used for 
        sending a magnetic flux into the qubit (for flux-tunable qubits such as 
        SNAILs)
    Returns:
        *results: type = dictionary, contents =  {
            "I": np.array(I), #values of real part of signal received
            "Q": np.array(Q), #values of imaginary part of signal received
            "program and parameters": program_and_parameters, #A dictionary of the qua program used 
                                                                and certain parameters
                                                                like the frequency range 
                                                                or time range that's used
            "experiment parameters": self.experiment_config[experiment_name],
            "OPX parameters": self.OPX_config
        }

    """
    def RUN_experiment(self, experiment_name, config, elementsAndGains = None, paramFile = "calibration_params.json", dc_current = None):
        
    
        #program_and_parameters = self.implemented_experiments[experiment_name](self.experiment_config[experiment_name])
        experiment_params = {**config[experiment_name], **config["__Shared Values__"]}
        
        fcommand = f"self.{experiment_name}({experiment_params})"
        program_and_parameters = eval(fcommand)
        prog = program_and_parameters["prog"]

        current_LO_freq = self.OPX_config["elements"]["resonator"]["mixInputs"]["lo_frequency"]


        u = unit()

        ###Starts the quantum machine with the parameters we have passed###
        # self.start_QM_octave(calibration=True, paramFile=paramFile)        
        
        ###Change the gain of elements
        if(elementsAndGains is not None):
            for element, gain in elementsAndGains.items():
                self.qm.octave.set_rf_output_gain(element, gain)
        ###Send a DC current into the qubit before we run our experiment 
        if dc_current is not None:
            currentSource = self.instrumentManager["YOKO1N"]
            currentSource.set_mode('CURR')
            currentSource.set_output(False)
            currentSource.set_measure_state(state = True)
            currentSource.set_current(dc_current)
            currentSource.set_output(True)

        ### Run experiment and get results 
        job = self.qm.execute(prog)
        res = job.result_handles
        res.wait_for_all_values()

        ### Turn off the current source once we have finished the experiment ###
        if dc_current is not None:
            currentSource.set_output(False)

        ### Convert I and Q signal to numpy arrays in Volts
        I = u.raw2volts(res.get("I").fetch_all())
        Q = u.raw2volts(res.get("I").fetch_all())

        ### Result dictionary that can be transformed into an h5py file
        results = {
            "I": np.array(I),
            "Q": np.array(Q),
            "program_name": experiment_name,
            "experiment parameters" : config,
            "OPX parameters": self.OPX_config
        }

        ### Adds all of the program parameters, ex: frequencies, times, etc, to the results dictionary ###
        for key in program_and_parameters:
            if key != "prog":
                results[key] = (str)(program_and_parameters[key])


        ### Final results dictionary ###
        return results
  
    """
    Allows you to save a results dictionary to an existing or a new h5py file.

    results(dict): dictionary of results, should be in the style of RUN_experiment's results dictionary being returned
    resultName(string): name of the dataset. Note, to find individual attributes of a dataset need to do dataset[resultName+"_"+attributeName]
    fileName(string): name of the h5py file, will create if it doesn't exist.
    path (string): path to h5py file directory.
    """
    def saveResults(self, results, resultName, fileName, path = ""):
        with h5py.File(path+fileName, "a") as f:
            for key in results:
                if(not isinstance(results[key], dict)):
                    f.create_dataset(resultName+"_"+key, data = results[key])
                else:
                    f.create_dataset(resultName+"_"+key, data = str(results[key]))

   
   


# nanoTest = Single_Qubit_Experiments()
# nanoTest.start_QM_octave(calibration=False)
# # # # results = nanoTest.editCalibrationParams("qubit", LOFrequencies=[5e9], IFFrequencies=[5e6]) 
# nanoTest.start_QM_octave(calibration=True)

# # nanoTest.RUN_experiment("qubitspec", experiment_config)
# # # nanoTest.saveResults(results, "test", "test")   

