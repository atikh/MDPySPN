<p align="center">
    <img src="https://img.shields.io/badge/contributions-welcome!-green" alt="Contributions welcome!"/>
</p>

# MDPySPN

# A lightweight tool for the simulation of Multidimensional Stochastic Petri Nets (MDSPN).

## Getting Started

:information_source: *Tested with Python 3.11*

### via git

```bash
git clone https://github.com/atikh/MDPySPN.git  # 1. Clone repository
pip install -r requirements.txt  # 2. Install requirements
python examples/Main.py  # 3. Run the code
```

## Modeling

We define the dimensions in interest and return the same as the following example:
```bash
Total_Dimensions = ['time', 'energy', 'waste']
```
The "time" dimension must always be listed first in the Total_Dimensions list and must be explicitly named "Time" (case-sensitive). 


Formally, the class of SPNs that can be modeled using *PySPN* is defined as:

$$SPN = (P, T, A, G, m_0)$$

where:

* $P = \{P_1,P_2,..,P_m\}$ is the set of places, drawn as circles;
* $T = \{T_1,T_2,..,T_n\}$ is the set of transitions along with their distribution functions or weights, drawn as bars;
* $A = A^I \cup A^O \cup A^H$ is the set of arcs, where $A^O$ is the set of output arcs, $A^I$ is the set of input arcs and $A^H$ is the set of inhibitor arcs and each of the arcs has a multiplicity assigned to it;
* $G = \{g_1,g_2,..,g_r\}$ is the set of guard functions that are associated with different transitions;
* and $m_0$ is the initial marking, defining the distribution of tokens in the places.

Each transition is represented as $T_i = (type, F)$, where $type \in \{timed,immediate\}$ indicates the type of the transition, and $F$ is either a probability distribution function if the corresponding transition is timed, or a firing weight or probability if it is immediate. 

Find sample SPNs under `examples/`. Currently, places, timed transitions (t\_type = "T"), immediate transitions (t\_type = "I"), output arcs, input arcs, inhibitor arcs, guard functions, and memory policies are supported.

### Places

A place with its required arguments is defined like so:
```bash
p1 = Place(label="Place 1", n_tokens=0)
```

To solve the conflict between time and other dimensions, when a place has a dependency on time dimension for consuming its dimension value and is linked to an immediate transition, we use DoT=1. This means while a token is in this place, the time is counted. When the transition fires, the duration that the token spent in the place will be multiplied by the rate of the transition for that dimension. This is especially useful for scenarios like an "Idle" state in an energy-dimension model.
```bash
pI1 = Place("Idle",1, DoT=1, dimension_tracked="energy")
```

### Transitions

A timed transition with its required arguments and a sample distribution function is defined as:
```bash
t1 = Transition(label="Transition 1", t_type="T")
t1.set_distribution(distribution="expon", a=0.0, b=1.0/1.0)
```

An immediate transition with its required arguments and a sample weight is defined as:
```bash
t2 = Transition(label="Transition 2", t_type="I")
t2.set_weight(weight=0.8)
```
Additionally, in this code, we define special transitions as "Multidimensional Transitions". These transitions are divided and showcase the behavior of the system in each dimension in the order of the dimensions introduced at the beginning of the code. For instance, in the example code the new order transition, is contributing in the time dimension which is white in the first part of the transition, and non-contributing in energy and waste dimensions which are shown in their parts in black.
To define which dimensions are affected by the transition we use "dimension_changes" which by default is None.
```bash
t3 = Transition("Processing", "T")
t3.add_dimension_change("energy", "rate", 25) # which shows this transition is contributing to the energy dimension.
t3.add_dimension_change("waste", "fixed",  20) # which shows this transition is contributing to the waste dimension.
```

We define specific input and output places within the model to track the system and also can be used as debugging items to check the transition behavior regarding the token destruction and generation.
```bash
t1 = Transition("Transition 1","T", input_transition=True)
tN = Transition("Transition N","T", output_transition=True)
```


For timed transitions, some of the supported distributions are:

| Distribution           | Parameter        |
|------------------------|------------------|
| Deterministic ("det")  | `a` (fixed delay)|
| Exponential ("expon")  | `a`, `b`         |
| Normal ("norm")        | `a`, `b`         |
| Lognormal ("lognorm")  | `a`, `b`, `c`    |
| Uniform ("uniform")    | `a`, `b`         |
| Triangular ("triang")  | `a`, `b`, `c`    |
| Weibull ("weibull_min")| `a`, `b`, `c`    |

More distributions can be easily implemented in `RNGFactory.py`. See [Scipy's documentation](https://docs.scipy.org/doc/scipy/reference/stats.html) for details regarding the distributions and their parameters.

Additionally, In our model, we define transitions that can affect the values of dimensions tracked by "dimension_holder" places. These transitions can induce changes in dimensions either by a fixed value or by a rate that is multiplied by time.

Each transition can be linked to one or more "dimension_holder" places, and the changes in these places are determined based on predefined values associated with the transitions. The types of changes that can occur are:

* Fixed Value Changes: The dimension increases or decreases by a specified fixed amount whenever the transition is fired.
* Rate-based Changes: The dimension changes at a specified rate, which is multiplied by the duration of time over which the transition occurs.

```bash
t2.set_distribution("expon", a=0.0, b=1.0/1.0)
t2.add_dimension_change("energy", "rate", 4)
t2.add_dimension_change("waste", "fixed", 20)
```


### Guard Functions for Transitions

Guard functions are defined like so:
```bash
def guard_t1():
    if len(p1.n_tokens) >= 2:
        return True
    else: return False
t1.set_guard_function(guard_t1)
```

### Memory Policies for Timed Transitions

The default setting is Race Enable ("ENABLE").

The memory policy can be set during instantiation
```bash
t1 = Transition(label="Transition_1",t_type="T",memory_policy="AGE")
```
or by using a function call
```bash
t1.set_memory_policy("AGE")
```

### Join  and Fork Transitions
To configure a transition that joins two or more input places, set the "Join" parameter to 1. 
This indicates that the transition will act upon the confluence of tokens from multiple places.
```bash
t1 = Transition(label="", t_type="", Join=1)
```
Similarly, to set up a transition that splits its output to multiple places, utilize the "Fork" parameter. 
Setting split to 1 designates that the transition's output will be distributed to several output places.
```bash
t1 = Transition(label="", t_type="", Fork=1)
```

## Export & Import of SPNs

Export and import SPNs as [pickle](https://docs.python.org/3/library/pickle.html) files using the `export_spn()` and `import_spn()` functions of `spn_io` module.

## Simulation

Simulate a SPN like so:
```bash
simulate(spn, max_time = 100, verbosity = 2, protocol = True)
```

For the verbosity, there are 3 levels of what is printed in the terminal:
 
* 0: No information;
* 1: Only final simulation statistics;
* 2: Initial markings, firing of transitions, and final statistics;  
* 3: Initial markings, firing of transitions and the resulting marking and state, and final statistics.

The simulation protocol capturing the markings throughout the simulation can be found under `output/protocol/`.

## Visualization

Visualize a Multidimensional SPN like so:
```bash
draw_spn(spn, show=False, file="sample_spn", rankdir="LR")
```
The graph can be found under `output/graphs/`. 

and 
The output can be defined as a visualization in the form of an MDSPN diagram, and the same to show the final places and dimension values in the terminal.
```bash
draw_spn(spn, show=True)
```
Sample multidimensional SPN graph:
![image](https://github.com/user-attachments/assets/5896cc0c-2ce2-422b-a00d-c69fca909c36)


At the end of the simulation run, if the **show** option is enabled, a **PDF file** will be generated containing a detailed visualization of the final state of the simulation. This graph includes key performance indicators (**KPIs**) such as **input/output statistics** and the **final A

## Multidimensional Event Log
MDPySPN provides a multidimensional event log as an output of the simulation. Each entry in a multidimensional event log captures a specific process step, such as the beginning or conclusion of an activity. It tracks changes across predefined dimensions, each noted as "dimension_stamp". This logging approach facilitates system analysis and supports multi-flow process mining, useful for data-driven simulation and Digital Twin model extraction. Following is the excerpt multidimensional event log of the simulation model:

![image](https://github.com/user-attachments/assets/6e317653-0848-4755-a36a-293ad5f375c1)


## Usage & Attribution

If you are using the tool for a scientific project please consider citing our [publication]
 #  - ...
    @misc{} 

For questions/feedback feel free to contact me: atieh.khodadadi@kit.edu


 
