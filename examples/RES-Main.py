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
from components.Dynamic_Guard import *

## Define Dimensions and return to all ##
#########################
Total_Dimensions = ['time', 'Energy', 'RES']

if __name__ == "__main__":
    spn = SPN()

#########################
## Define Places and Transitions ##
#########################
    p1 = Place("P RES Update", n_tokens=1)
    p2 = Place("P New Tasks", n_tokens=0)
    p3 = Place("P Production", n_tokens=0)
    p5 = Place("P Task Completed", n_tokens=0)



    Mt1 = Transition("RES Update","T", input_transition=True)
    Mt1.set_distribution("det", a=1)
    Mt1.add_dimension_change("RES", "dynamicRate", "karlsruhe_next_hours_egr.csv", "EGR_kWh")

    Mt2 = Transition("New Task", "T", input_transition=True)
    Mt2.set_distribution("det", a=10)

    Mt3 = Transition("Production with Grid Power", "T")
    Mt3.set_distribution("triang", a=0.5, b=4.0, c=2.0)
    Mt3.add_dimension_change("Energy", "rate", 0.02)

    Mt4 = Transition("Production with RES Power", "T")
    Mt4.set_distribution("triang", a=0.5, b=4.0, c=2.0)
    Mt4.add_dimension_change("RES", "rate", -0.02)

    set_resource_xor_guards(spn, resource_option_t=Mt4, fallback_option_t=Mt3,
        resource_activity_t=Mt3, resource_rate=0.02,  resource_dim="RES")

    Mt5 = Transition("Production with Grid Completed", "T", output_transition=True)
    Mt5.set_distribution("det", a=1)




#########################
##     ADD PLACES      ##
#########################
    spn.add_place(p1)
    spn.add_place(p2)
    spn.add_place(p3)
    spn.add_place(p5)



#########################
##   ADD Transitions   ##
#########################
    spn.add_transition(Mt1)
    spn.add_transition(Mt2)
    spn.add_transition(Mt3)
    spn.add_transition(Mt4)
    spn.add_transition(Mt5)


#########################
##      ADD links      ##
#########################
    spn.add_input_arc(p1,Mt1)
    spn.add_output_arc(Mt1,p1)

    spn.add_output_arc(Mt2,p2)
    spn.add_input_arc(p2,Mt3)
    spn.add_input_arc(p2,Mt4)
    spn.add_output_arc(Mt3,p3)
    spn.add_output_arc(Mt4,p3)
    spn.add_input_arc(p3,Mt5)
    spn.add_output_arc(Mt5,p5)





#########################
## Simulation Settings ##
#########################
    print("Before simulation")
    simulate(spn, max_time=540, verbosity=1, protocol=True) #8:00-17:00=9 hours=>*60=540
    print("After simulation")

#print_petri_net(spn)
    draw_spn(spn, show=True)