# MDPySPN
A lightweight tool for Multi-Dimensional Stochastic Petri Nets Simulation in Python.
MDPySPN is an extended version of PySPN which you can find in the following link:
https://github.com/jo-chr/pyspn

## Getting Started

:information_source: *Tested with Python 3.11*

### via git

```bash
git clone https://github.com/atikh/MDPySPN  # 1. Clone repository
pip install -r requirements.txt  # 2. Install requirements
python3 examples/Main.py  # 3. Run the example code
```

## Modeling
Initially, we define the dimensions in our model:
Total_Dimensions = ['time', 'energy', 'waste']

Formally, the class of SPNs that can be modeled using *MDPySPN* is defined as:

$$SPN = (P, T, A, G, m_0)$$

where:

* $P = \{P_1,P_2,..,P_m\}$ is the set of places, drawn as circles;
* $T = \{T_1,T_2,..,T_n\}$ is the set of transitions along with their distribution functions or weights, drawn as bars;
* $A = A^I \cup A^O \cup A^H$ is the set of arcs, where $A^O$ is the set of output arcs, $A^I$ is the set of input arcs and $A^H$ is the set of inhibitor arcs and each of the arcs has a multiplicity assigned to it;
* $G = \{g_1,g_2,..,g_r\}$ is the set of guard functions which are associated with different transitions;
* and $m_0$ is the initial marking, defining the distribution of tokens in the places.

Each transition is represented as $T_i = (type, F)$, where $type \in \{timed,immediate\}$ indicates the type of the transition, and $F$ is either a probability distribution function if the corresponding transition is timed, or a firing weight or probability if it is immediate. 

Find sample SPNs under `examples/`. Currently, places, timed transitions (t\_type = "T"), immediate transitions (t\_type = "I"), output arcs, input arcs, inhibitor arcs, guard functions, and memory policies are supported.

### Places

A place with its required arguments is defined like so:
```bash
p1 = Place(label="Place 1", n_tokens=0)
```
In this code, we define special places known as "dimension_holder" places. These places are responsible for tracking the effects of certain transitions on specific dimensions when they are fired. The dimension that each "dimension_holder" place monitors is specified by the "dimension_tracked" attribute.
p3 = Place(label="PH1", is_dimension_holder=True, dimension_tracked='energy', initial_value=0)


### Transitions

A timed transition with its required arguments and a sample distribution function is defined like so:
```bash
t1 = Transition(label="Transition 1", t_type="T")
t1.set_distribution(distribution="expon", a=0.0, b=1.0/1.0)
```

An immediate transition with its required arguments and a sample weight is defined like so:
```bash
t2 = Transition(label="Transition 2", t_type="I")
t2.set_weight(weight=0.8)
```

In our multi-dimensional model, we define transitions that can affect the values of dimensions tracked by "dimension_holder" places. These transitions can induce changes in dimensions either by a fixed value or by a rate that is multiplied by time.
Each transition can be linked to one or more "dimension_holder" places, and the changes in these places are determined based on predefined values associated with the transitions. The types of changes that can occur are:

* Fixed Value Changes: The dimension increases or decreases by a specified fixed amount whenever the transition is fired.
* Rate-based Changes: The dimension changes at a specified rate, multiplied by the duration of time over which the transition occurs.
t2.add_dimension_change("energy", "rate", 4)
t2.add_dimension_change("waste", "fixed",  20)

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

For the verbosity there are 3 levels of what is printed in the terminal:
 
* 0: No information;
* 1: Only final simulation statistics;
* 2: Initial markings, firing of transitions, and final statistics;  
* 3: Initial markings, firing of transitions and the resulting marking and state, and final statistics.

The simulation protocol capturing the markings throughtout the simulation can be found under `output/protocol/`.

## Visualization

Visualize a SPN like so:
```bash
draw_spn(spn, show=False, file="sample_spn", rankdir="LR")
```
The graph can be found under `output/graphs/`. 

## Usage & Attribution
