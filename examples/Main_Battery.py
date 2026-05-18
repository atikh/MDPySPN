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



## Define Dimensions and return to all ##
#########################
Total_Dimensions = ['Time', 'Grid', 'Battery']

Subdimensions = {
    'Battery': ['Battery.AGV1', 'Battery.AGV2']
}

initial_dimension_values = {
    "Battery.AGV1": 100.0,
    "Battery.AGV2": 100.0
}


if __name__ == "__main__":
    spn = SPN(dimensions=Total_Dimensions, subdimensions=Subdimensions, initial_dimension_values=initial_dimension_values) #HERE Important

#########################
## Define Places and Transitions ##
#########################
    pI1 = Place("AGV1 Idle", 1, DoT=1, dimension_tracked="Battery.AGV1")
    pI2 = Place("AGV2 Idle", 1, DoT=1, dimension_tracked="Battery.AGV2")

    p1 = Place("New Tasks")

    p2 = Place("AGV1 Ready")
    p3 = Place("AGV2 Ready")

    p4 = Place("AGV1 Charging Ready")
    p5 = Place("AGV2 Charging Ready")

    p6 = Place("End 1")
    p7 = Place("End 2")



    Mt1 = Transition("New Task","T", input_transition=True)
    Mt1.set_distribution("det", a=2)

    Mt2 = Transition("Select AGV1","I")
    Mt2.add_dimension_change("Battery.AGV1", "rate", -0.2)
    Mt2.set_weight(weight=0.5)

    Mt3 = Transition("Select AGV2", "I")
    Mt3.add_dimension_change("Battery.AGV2", "rate", -0.2)
    Mt3.set_weight(weight=0.5)


    Mt4 = Transition("AGV1 Transport", "T")
    Mt4.set_distribution("det", a=1)
    Mt4.add_dimension_change("Battery.AGV1", "rate", -0.2)
    Mt5 = Transition("AGV2 Transport", "T")
    Mt5.set_distribution("det", a=1)
    Mt5.add_dimension_change("Battery.AGV2", "rate", -0.2)



    Mt8 = Transition("AGV1 Idle to charging", "I")
    Mt8.add_dimension_change("Battery.AGV1", "rate", -0.2)
    def guard_t1():
        return spn.get_dimension_value("Battery.AGV1") < 20.0

    Mt8.set_guard_function(guard_t1)

    Mt9 = Transition("AGV2 Idle to charging", "I")
    Mt9.add_dimension_change("Battery.AGV2", "rate", -0.2)
    def guard_t2():
        return spn.get_dimension_value("Battery.AGV2") < 20.0

    Mt9.set_guard_function(guard_t2)

    Mt10 = Transition("AGV1 Charging Complete", "T")
    Mt10.set_distribution("charging", r=2, max_charging=100.0, battery_dim="Battery.AGV1")
    Mt10.add_dimension_change("Grid", "rate", 0.5)

    Mt11 = Transition("AGV2 Charging Complete", "T")
    Mt11.set_distribution("charging", r=2, max_charging=100.0, battery_dim="Battery.AGV2")
    Mt11.add_dimension_change("Grid", "rate", 0.5)
#########################
##     ADD PLACES      ##
#########################
    spn.add_place(p1)
    spn.add_place(pI1)
    spn.add_place(pI2)
    spn.add_place(p2)
    spn.add_place(p3)
    spn.add_place(p4)
    spn.add_place(p5)
    spn.add_place(p6)
    spn.add_place(p7)


#########################
##   ADD Transitions   ##
#########################
    spn.add_transition(Mt1)
    spn.add_transition(Mt2)
    spn.add_transition(Mt3)
    spn.add_transition(Mt4)
    spn.add_transition(Mt5)
    spn.add_transition(Mt8)
    spn.add_transition(Mt9)
    spn.add_transition(Mt10)
    spn.add_transition(Mt11)


#########################
##      ADD links      ##
#########################
    spn.add_output_arc(Mt1,p1)
    spn.add_input_arc(p1,Mt2)
    spn.add_input_arc(p1,Mt3)
    spn.add_output_arc(Mt2,p2)
    spn.add_output_arc(Mt3,p3)
    spn.add_input_arc(p2,Mt4)
    spn.add_input_arc(p3,Mt5)


    spn.add_input_arc(pI1,Mt2)
    spn.add_input_arc(pI2,Mt3)
    spn.add_output_arc(Mt4,pI1)
    spn.add_output_arc(Mt5,pI2)
    spn.add_output_arc(Mt4,p6)
    spn.add_output_arc(Mt5,p7)

    spn.add_input_arc(pI1, Mt8)
    spn.add_input_arc(pI2, Mt9)
    spn.add_output_arc(Mt8,p4)
    spn.add_output_arc(Mt9,p5)
    spn.add_input_arc(p4,Mt10)
    spn.add_input_arc(p5,Mt11)
    spn.add_output_arc(Mt10,pI1)
    spn.add_output_arc(Mt11,pI2)
#########################
## Simulation Settings ##
#########################
    simulate(
        spn,
        max_time=480,
        verbosity=1,
        protocol=True,
        Dimensions=spn.executable_dimensions
    )
    #HERE Is Important

#print_petri_net(spn)
    draw_spn(spn, show=True)

