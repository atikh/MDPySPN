import sys
sys.path.append('C:/Users/iu4647/Models/MDSPN/03- pyspn-main- with IDLE')

#########################
## Define Dimensions and return to all ##
#########################
Total_Dimensions = ['time', 'energy', 'waste']
#########################
## Imports ##
#########################
from components.spn import *
from components.spn_simulate import simulate
from components.spn_io import print_petri_net
from components.spn_visualization import *
from components.spn import SPN
spn = SPN()

#########################
## Define Places and Transitions ##
#########################
p1 = Place("Preprocess",0)
pI1 = Place("Idle",1, DoT=1, dimension_tracked="energy") #Define Related Dimension of Time
p2 = Place("Production Process",0)
p3 = Place(label="PhEnegery1", is_dimension_holder=True, dimension_tracked='energy', initial_value=0)
p4 = Place(label="PhWaste1", is_dimension_holder=True, dimension_tracked='waste', initial_value=0)
p5 = Place(label="PhEnegery2", is_dimension_holder=True, dimension_tracked='energy', initial_value=0)

t1 = Transition("Arrive","T")
t1.set_distribution("det", a=4.0, b=1.0/1.0)

t2 = Transition("Preprocesses", "T", Fork=1)
t2.set_distribution("expon", a=0.0, b=1.0/1.0)
t2.add_dimension_change("energy", "rate", 4)
t2.add_dimension_change("waste", "fixed",  20)



t3 = Transition("Approach_Server2", "I")
t3.add_dimension_change("energy", "fixed", 110)



#########################
##     ADD PLACES      ##
#########################
spn.add_place(p1)
spn.add_place(pI1)
spn.add_place(p2)
spn.add_place(p3)
spn.add_place(p4)
spn.add_place(p5)

#########################
##   ADD Transitions   ##
#########################
spn.add_transition(t1)
spn.add_transition(t2)
spn.add_transition(t3)



#########################
##      ADD links      ##
#########################
spn.add_output_arc(t1,p1)
spn.add_input_arc(p1,t2)
spn.add_input_arc(pI1,t2)
spn.add_output_arc(t2,p2)
spn.add_output_arc(t2,p3)
spn.add_output_arc(t2,p4)
spn.add_output_arc(t2,pI1)
spn.add_input_arc(p2,t3)
spn.add_output_arc(t3,p5)



#########################
## Simulation Settings ##
#########################
simulate(spn, max_time = 20, verbosity = 2, protocol = True)

#print_petri_net(spn)
draw_spn(spn, show=True)
spn.report_places()