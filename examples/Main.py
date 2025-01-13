import sys
sys.path.append('MDSPN') # please provide the path



#########################
## Imports ##
#########################
from MDPySPN.components.spn import *
from components.spn_simulate import simulate
from components.spn_visualization import *
from components.spn import SPN

## Define Dimensions and return to all ##
#########################
Total_Dimensions = ['time', 'energy', 'waste']

spn = SPN()

#########################
## Define Places and Transitions ##
#########################
p1 = Place("New Tasks",0)
pI1 = Place("Idle",1, DoT=1, dimension_tracked="energy")
p2 = Place("Production Process",0)
p3= Place("Production Done",0)
pE1 = Place(label="Tracking Place Enegery1", is_tracking=True, dimension_tracked='energy', initial_value=0)
pW1 = Place(label="Tracking Place Waste1", is_tracking=True, dimension_tracked='waste', initial_value=0)
pE2 = Place(label="Tracking Place Enegery2", is_tracking=True, dimension_tracked='energy', initial_value=0)

t1 = Transition("New Task","T", input_transition=True)
t1.set_distribution("expon", a=7.0, b=1.0/1.0)
t2 = Transition("Preprocessing","I", Fork=1)
t2.add_dimension_change("energy", "rate", 4)
t3 = Transition("Processing", "T", Fork=1, capacity=10)
t3.set_distribution("det", a=7)
t3.add_dimension_change("energy", "rate", 25)
t3.add_dimension_change("waste", "fixed",  20)
t4 = Transition("Task Completed", "I", output_transition=True)


#########################
##     ADD PLACES      ##
#########################
spn.add_place(p1)
spn.add_place(pI1)
spn.add_place(p2)
spn.add_place(p3)
spn.add_place(pE1)
spn.add_place(pW1)
spn.add_place(pE2)


#########################
##   ADD Transitions   ##
#########################
spn.add_transition(t1)
spn.add_transition(t2)
spn.add_transition(t3)
spn.add_transition(t4)


#########################
##      ADD links      ##
#########################
spn.add_output_arc(t1,p1)
spn.add_input_arc(p1,t2)
spn.add_input_arc(pI1,t2)
spn.add_output_arc(t2,p2)
spn.add_output_arc(t2,pE1)
spn.add_input_arc(p2,t3)
spn.add_output_arc(t3,p3)
spn.add_output_arc(t3,pE2)
spn.add_output_arc(t3,pW1)
spn.add_output_arc(t3,pI1)
spn.add_input_arc(p3,t4)



#########################
## Simulation Settings ##
#########################
simulate(spn, max_time = 100, verbosity = 2, protocol = True)

#print_petri_net(spn)
draw_spn(spn, show=True)
spn.report_places()
