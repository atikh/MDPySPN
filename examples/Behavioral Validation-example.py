import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent                        # one folder above
sys.path.insert(0, str(PARENT_DIR))
#########################/
## Imports ##
#########################
from components.spn import *
from components.spn_simulate import simulate
from components.spn_visualization import *
from components.spn import SPN


# ---------------------------------------
# 1. Define dimensions
# ---------------------------------------
Total_Dimensions = [
    "time",
    "Battery state",
    "Grid use",
    "Cost"
]

spn = SPN(
    dimensions=Total_Dimensions,
    initial_dimension_values={
        "Battery state": 40.0,
        "Grid use": 0.0,
        "Cost": 0.0
    }
)

# ---------------------------------------
# 2. Define places
# ---------------------------------------
p1 = Place("Waiting Jobs", 2)
p2 = Place("Robot Idle", 1)
p3 = Place("Robot Processing", 0)
p4 = Place("Completed Jobs", 0)
p5 = Place("Robot Charging", 0)

# ---------------------------------------
# 3. Define transitions
# ---------------------------------------

# Mt1: Start Processing (immediate)
Mt1 = Transition("Start Processing", "I")
Mt1.set_guard_function(
    lambda: spn.get_dimension_value("Battery state") > 30
)

# Mt2: Complete Processing (timed)
Mt2 = Transition("Complete Processing", "T")
Mt2.set_distribution("det", a=3)

Mt2.add_dimension_change("Battery state", "fixed", -15)
Mt2.add_dimension_change("Grid use", "rate", 2)
Mt2.add_dimension_change("Cost", "fixed", 4)

# Mt3: Start Charging (immediate)
Mt3 = Transition("Start Charging", "I")
Mt3.set_guard_function(
    lambda: (
        spn.get_dimension_value("Battery state") <= 30
        and len(p1.tokens) > 0
    )
)

# Mt4: Complete Charging (timed)
Mt4 = Transition("Complete Charging", "T")
Mt4.set_distribution("det", a=2)

Mt4.add_dimension_change("Battery state", "fixed", 20)

# ---------------------------------------
# 4. Add places
# ---------------------------------------
for p in [p1, p2, p3, p4, p5]:
    spn.add_place(p)

# ---------------------------------------
# 5. Add transitions
# ---------------------------------------
for t in [Mt1, Mt2, Mt3, Mt4]:
    spn.add_transition(t)

# ---------------------------------------
# 6. Add connections
# ---------------------------------------

# Start processing
spn.add_input_arc(p1, Mt1)
spn.add_input_arc(p2, Mt1)
spn.add_output_arc(Mt1, p3)

# Complete processing
spn.add_input_arc(p3, Mt2)
spn.add_output_arc(Mt2, p2)
spn.add_output_arc(Mt2, p4)

# Start charging
spn.add_input_arc(p2, Mt3)
spn.add_output_arc(Mt3, p5)

# Complete charging
spn.add_input_arc(p5, Mt4)
spn.add_output_arc(Mt4, p2)

# ---------------------------------------
# 7. Run simulation
# ---------------------------------------
if __name__ == "__main__":

    simulate(
        spn,
        max_time=10,
        verbosity=2,
        protocol=True,
        event_log=True,
        Dimensions=Total_Dimensions
    )


#print_petri_net(spn)
    draw_spn(spn, show=True)

    print("\nFinal marking:")
    for p in spn.places:
        print(p.label, len(p.tokens))

