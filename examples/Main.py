import sys

sys.path.append('../MDPySPN')
#########################/
## Imports ##
#########################
from components.spn import *
from components.spn_simulate import simulate
from components.spn_visualization import *
from components.spn import SPN



## Define Dimensions and return to all ##
#########################
Total_Dimensions = ['time', 'Energy', 'Waste']

if __name__ == "__main__":
    spn = SPN()

#########################
## Define Places and Transitions ##
#########################
    p1 = Place("New Tasks")
    pI1 = Place("Idle",1, DoT=1, dimension_tracked="Energy")
    p2 = Place("Production Process")
    p3= Place("Production Done")

    Mt1 = Transition("New Task","T", input_transition=True)
    Mt1.set_distribution("expon", a=2, b=1.0/1.0)
    Mt2 = Transition("Preprocessing (begin)","I", Join=1)
    Mt2.add_dimension_change("Energy", "rate", 25)
    Mt3 = Transition("Processing (begin)", "T", Fork=1)
    Mt3.set_distribution("det", a=2)
    Mt3.add_dimension_change("Energy", "rate", 50)
    Mt3.add_dimension_change("Waste", "fixed",  1.5)
    Mt4 = Transition("Task Completed", "I", output_transition=True)


#########################
##     ADD PLACES      ##
#########################
    spn.add_place(p1)
    spn.add_place(pI1)
    spn.add_place(p2)
    spn.add_place(p3)


#########################
##   ADD Transitions   ##
#########################
    spn.add_transition(Mt1)
    spn.add_transition(Mt2)
    spn.add_transition(Mt3)
    spn.add_transition(Mt4)


#########################
##      ADD links      ##
#########################
    spn.add_output_arc(Mt1,p1)
    spn.add_input_arc(p1,Mt2)
    spn.add_input_arc(pI1,Mt2)
    spn.add_output_arc(Mt2,p2)
    spn.add_input_arc(p2,Mt3)
    spn.add_output_arc(Mt3,p3)
    spn.add_output_arc(Mt3,pI1)
    spn.add_input_arc(p3,Mt4)



#########################
## Simulation Settings ##
#########################
    print("Before simulation")
    simulate(spn, max_time=100, verbosity=2, protocol=True)
    print("After simulation")

#print_petri_net(spn)
    draw_spn(spn, show=True)

