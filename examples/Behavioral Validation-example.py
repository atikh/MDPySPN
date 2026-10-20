
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
sys.path.insert(0, str(PARENT_DIR))

from components.spn import SPN, Place, Transition
from components.spn_simulate import simulate
from components.spn_visualization import draw_spn

# ---------------------------------------
# 1. Define dimensions
# ---------------------------------------
Total_Dimensions = [
    "time",
    "Cost",
    "Grid use",
    "Battery"
]

spn = SPN(
    dimensions=Total_Dimensions,
    initial_dimension_values={
        "Cost": 0.0,
        "Grid use": 0.0,
        "Battery": 40.0
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

# MT1: Preprocess (immediate)
Mt1 = Transition("Preprocess", "I", asset_level=True)

Mt1.set_guard_function(
    lambda: spn.get_dimension_value("Battery") > 30
)

Mt1.add_dimension_change(
    "Battery", "fixed", -15
)

# MT2: Process (timed)
Mt2 = Transition("Process", "T")
Mt2.set_distribution("det", a=3)

Mt2.add_dimension_change(
    "Cost", "fixed", 4
)

# MT3: Start Charging (immediate)
Mt3 = Transition("Start Charging", "I")

Mt3.set_guard_function(
    lambda: (
        spn.get_dimension_value("Battery") <= 30
        and len(p1.tokens) > 0
    )
)

# MT4: Charging (timed)
Mt4 = Transition("Charging", "T")
Mt4.set_distribution("det", a=2)

Mt4.add_dimension_change(
    "Battery", "fixed", 20
)

Mt4.add_dimension_change(
    "Grid use", "rate", 2
)

# ---------------------------------------
# 4. Add places and transitions
# ---------------------------------------
for p in [p1, p2, p3, p4, p5]:
    spn.add_place(p)

for t in [Mt1, Mt2, Mt3, Mt4]:
    spn.add_transition(t)

# ---------------------------------------
# 5. Add connections
# ---------------------------------------

# MT1: Preprocess
spn.add_input_arc(p1, Mt1)
spn.add_input_arc(p2, Mt1)
spn.add_output_arc(Mt1, p3)

# MT2: Process
spn.add_input_arc(p3, Mt2)
spn.add_output_arc(Mt2, p2)
spn.add_output_arc(Mt2, p4)

# MT3: Start Charging
spn.add_input_arc(p2, Mt3)
spn.add_output_arc(Mt3, p5)

# MT4: Charging
spn.add_input_arc(p5, Mt4)
spn.add_output_arc(Mt4, p2)

# ---------------------------------------
# 6. Run simulation
# ---------------------------------------
if __name__ == "__main__":

    os.chdir(BASE_DIR)

    simulate(
        spn,
        max_time=10,
        verbosity=2,
        protocol=True,
        event_log=True,
        Dimensions=Total_Dimensions
    )

    draw_spn(spn, show=True)

    print("\nFinal marking:")
    for p in spn.places:
        print(p.label, len(p.tokens))

    print("\nFinal dimension values:")
    for dim in ["Cost", "Grid use", "Battery"]:
        print(dim, spn.get_dimension_value(dim))
