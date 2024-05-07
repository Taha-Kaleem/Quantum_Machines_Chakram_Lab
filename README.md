In Dr. Srivatsan Chakram's lab, we use a Quantum Machines OPX and Octave setup for running experiments (listed in experiments.json)

To find more information on the OPX/Octave, check the documentation for Quantum Machines (https://docs.quantum-machines.co/1.1.7/)
and the github page (https://github.com/qua-platform).

In our lab we run experiments using the Single_Qubit_Experiments_Results notebook. Right now we have implemented 5 experiments, which
can be run in the notebook. These experiments are for a single qubit coupled to a readout resonator and are implemented in the 
OPXexperiments.py file.

OPX/Octave configuration parameters can be changed in the oldConfig.py file and experimental parameters in the experiments.json file.
We can also alter mixer calibration parameters in the calibration_params.json file (see quantum machines documentation for more
information on mixer calibratioN).
