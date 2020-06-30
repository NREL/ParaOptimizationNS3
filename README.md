# ParaOptimizationNS3
Parameter Optimization Framework for NS-3 network optimization

### Dependencies
This software assumes the following prerequisites are available on the host system:

* [Python](https://www.python.org/) - Interpreted programming language  

* [ns3](https://www.nsnam.org/) - Event-driven Network Simulator


### Usage
First, the ns3 module qos-app must be added to the ns3 src/ folder and then ns3 must be rebuilt.
Note:- The ns3 model under test must implement at minimum the client and server ns3 application models for this to work

### Genetic Optimizer Parameters

* MutationChance (%): The percentage chance of a mutation occuring per trait 

* MutationRate (%): The percentage variation possible from the original trait due to a mutation. This only affects numerical traits.

* MaxElite : The number of Elites allowed for breeding future generations.

* MaxPopulation : The Maximum number of number of potential parents

* MaxGeneration : The maximum number of generations which will be run

* StepSize : The minimum numerical difference between child traits when optimizing using gradient descent method


### Results
Results are stored in different locations depending on their aggregation level:

* Raw_Results : Stores each result for individual runs of the model
* Av_Results : Stores each run result which consists of averaged result from each device across the run
* Optimal_Results : Stores optimal result of each generation which consists of lowest cost result from each device across the run


### Publications
The following publication has been released detailing this software. Please cite this paper if publishing any work using this tool:
```
A. Hasandka, J. Zhang, S. M. S. Alam, A. R. Florita and B. Hodge, "Simulation-based Parameter Optimization Framework 
for Large-Scale Hybrid Smart Grid Communications Systems Design," 2018 IEEE International Conference 
on Communications, Control, and Computing Technologies for Smart Grids (SmartGridComm), Aalborg, 2018, pp. 1-7.
doi: 10.1109/SmartGridComm.2018.8587472
```





 


