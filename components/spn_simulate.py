import random
import os

from .spn import *
from .spn_io import *
from .RNGFactory import *

SIMULATION_TIME = 0
SIMULATION_TIME_UNIT = None
VERBOSITY = 0
PROTOCOL = False
SCHEDULE_ITERATOR = 0

# Global list to track places with DoT
tracking_places = []

def marking(place: Place) -> int:
    return place.n_tokens

def mean_tokens(place: Place) -> float:
    return place.total_tokens/SIMULATION_TIME

def p_not_empty(place: Place) -> float:
    return place.time_non_empty/SIMULATION_TIME

def p_enabled(transition: Transition) -> float:
    return transition.time_enabled/SIMULATION_TIME

def n_firings(transtion: Transition) -> int:
    return transtion.n_times_fired

def throughput(transition: Transition) -> float:
    return transition.n_times_fired/SIMULATION_TIME

def add_tokens(place: Place, n_tokens: int):
    # Assuming `tokens` is a list of token IDs in the Place class

    if PROTOCOL == True:
        # Write the protocol with the ID of the last added token, if any, or 'None'
        last_token_id = place.tokens[-1] if place.tokens else 'None'
        print("MAX",place.tokens, place.label)
        write_to_protocol(place.label, SIMULATION_TIME, len(place.tokens))
        write_to_event_log(SIMULATION_TIME, last_token_id, place.label)

    # Update statistics calculations using the current_number_of_tokens instead of place.n_tokens
    place.total_tokens += len(place.tokens) * (SIMULATION_TIME - place.time_changed)
    if len(place.tokens) > 0:
        place.time_non_empty += SIMULATION_TIME - place.time_changed

    place.time_changed = SIMULATION_TIME
    place.n_tokens=len(place.tokens)
    place.n_tokens += n_tokens

    # Handle the addition of new tokens
    for _ in range(n_tokens):
        new_token_id = ... # Generate a new token ID here, as per your token generation logic
        place.tokens.append(new_token_id)

    if len(place.tokens) > place.max_tokens:
        place.max_tokens = len(place.tokens)

    # Correctly calling write_to_protocol at the end of the function
    if PROTOCOL:
        write_to_protocol(place.label, SIMULATION_TIME, place.n_tokens)
        write_to_event_log(SIMULATION_TIME, last_token_id, place.label)


def sub_tokens(place: Place, n_tokens: int):
    if PROTOCOL == True:
        write_to_protocol(place.label,SIMULATION_TIME,place.n_tokens)
        write_to_event_log(SIMULATION_TIME, last_token_id, place.label)
    place.total_tokens += place.n_tokens*(SIMULATION_TIME-place.time_changed)
    if place.n_tokens > 0:
        place.time_non_empty += (SIMULATION_TIME-place.time_changed)
    place.time_changed = SIMULATION_TIME
    place.n_tokens -= n_tokens
    if place.n_tokens < 0:
        print("Negative number of tokens in Place {}".format(place))
    if PROTOCOL == True:
        write_to_protocol(place.label,SIMULATION_TIME,place.n_tokens)
        write_to_event_log(SIMULATION_TIME, last_token_id, place.label)

def get_initial_marking(spn: SPN):
    marking = {}
    for place in spn.places:
        place: Place
        # Instead of n_tokens, we store a copy of the current token IDs for each place
        marking[place] = list(place.tokens)  # Assuming `tokens` is a list of token IDs
    return marking


def set_initial_marking(spn: SPN, marking):
    for place in spn.places:
        place:Place
        place.n_tokens = marking[place]

def reset_state(spn: SPN, marking):
    for place in spn.places:
        place:Place
        place.n_tokens = 0
        place.time_changed = 0.0
        place.total_tokens = 0.0
        place.time_non_empty = 0.0
    
    for transition in spn.transitions:
        transition:Transition
        transition.time_enabled = 0
        transition.n_times_fired = 0
        transition.enabled_at = 0
        transition.enabled = False
    
    set_initial_marking(spn, marking)

def complete_statistics(spn: SPN):
    for place in spn.places:
        add_tokens(place, 0)
    for transition in spn.transitions:
        transition: Transition
        if transition.enabled == True:
            transition.time_enabled += SIMULATION_TIME - transition.enabled_at

def set_firing_time(transition: Transition):
    """Sets the firing time of a transition based on the transition type and distribution"""
    global SCHEDULE_ITERATOR

    transition.enabled_at = SIMULATION_TIME

    if transition.t_type == "I":
        transition.firing_delay = 0.0
    elif transition.t_type == "T":
        dist = list(transition.distribution.keys())[0]
        parameters = list(transition.distribution[dist].values())
        match dist:
            case "det":
                transition.firing_delay = get_delay("det", parameters[0])   
            case "uniform":
                transition.firing_delay = get_delay("uniform", parameters[0], parameters[1])
            case "expon":
                transition.firing_delay = get_delay("expon", parameters[0], parameters[1])
            case "norm":
                transition.firing_delay = get_delay("norm", parameters[0], parameters[1])
            case "lognorm":
                transition.firing_delay = get_delay("lognorm", parameters[0], parameters[1], parameters[2])
            case "triang":
                transition.firing_delay = get_delay("triang", parameters[0], parameters[1], parameters[2])
            case "cauchy":
                transition.firing_delay = get_delay("cauchy", parameters[0], parameters[1])
            case "exponpow":
                transition.firing_delay = get_delay("exponpow", parameters[0], parameters[1], parameters[2])
            case "gamma":
                transition.firing_delay = get_delay("gamma", parameters[0], parameters[1], parameters[2])
            case "weibull_min":
                transition.firing_delay = get_delay("weibull_min", parameters[0], parameters[1], parameters[2])
            case _:
                raise Exception("Distribution undefined for transition {}".format(transition))
            
    if transition.handicap != 1:
        if transition.handicap_type == "increase":
            transition.firing_delay = round(transition.handicap,2)*transition.firing_delay
        elif transition.handicap_type == "decrease":
            transition.firing_delay = transition.firing_delay/round(transition.handicap,2)

    
    if transition.t_type == "T" and SIMULATION_TIME_UNIT != None:
        transition.firing_delay = convert_delay(transition.firing_delay, time_unit=transition.time_unit, simulation_time_unit=SIMULATION_TIME_UNIT)

    transition.firing_time = transition.enabled_at + transition.firing_delay

def set_reset_time(transition: Transition):
    transition.reset_time = transition.enabled_at + transition.reset_threshold

def convert_delay(delay, time_unit = None, simulation_time_unit = None):
    if time_unit == "d" and simulation_time_unit == "h":
        return delay * 24
    else:
        return delay


def is_enabled(transition: Transition):
    """Checks whether a transition is currently enabled"""
    input_arcs = transition.input_arcs
    inhibitor_arcs = transition.inhibitor_arcs

    # Check each input arc to see if the from_place has any tokens
    for arc in input_arcs:
        if len(arc.from_place.tokens) >= arc.multiplicity:  # Ensure enough tokens are available
            continue
        else:
            return False

    # Assuming the logic for inhibitor arcs remains the same, unless they also use the tokens list
    for arc in inhibitor_arcs:
        if len(arc.from_place.tokens) >= arc.multiplicity:  # Adjusted for token list handling
            return False

    # If the transition has a guard function, its logic might also need adjustment
    if transition.guard_function is not None:
        return transition.guard_function()

    return True


def update_enabled_flag(spn: SPN):
    """Updates the enabled flag for all transitions in a SPN"""
    transition: Transition
    found_enabled = False

    for transition in spn.transitions:
        if is_enabled(transition) == False:
            #Transition is Race Enable and has just become disabled
            if transition.enabled == True and transition.memory_policy == "AGE":
                transition.disabled_at = SIMULATION_TIME
                transition.clock_active = True

            transition.enabled = False

    for transition in spn.transitions:
        if is_enabled(transition) == True:
            #Transition has just become enabled
            if transition.enabled == False:
                if transition.clock_active == True:
                    transition.disabled_time += SIMULATION_TIME - transition.disabled_at
                else: set_firing_time(transition)
            transition.enabled = True
            found_enabled = True

    return found_enabled


def fire_transition(transition: Transition):
    """Fires a transition, moving or generating tokens as described."""
    global tracking_places  # Access the global tracking list

    # Track the entrance time and place details for DoT places
    for oarc in transition.output_arcs:
        if oarc.to_place.DoT == 1:
            # Ensure not to add duplicates
            if not any(entry["place"] == oarc.to_place for entry in tracking_places):
                tracking_places.append({
                    "place": oarc.to_place,
                    "dimension": oarc.to_place.dimension_tracked,
                    "entrance_time": SIMULATION_TIME
                })

    # Calculate the maximum number of tokens that can be transferred, respecting the transition's capacity
    max_tokens_to_transfer = transition.capacity if transition.capacity is not None else float('inf')

    tokens_moved = 0  # Track the number of tokens moved in this firing

    if transition.Fork == 1:
        for iarc in transition.input_arcs:
            tokens_to_move = min(len(iarc.from_place.tokens), max_tokens_to_transfer)
            if PROTOCOL:  # Log the state before tokens start moving
                write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
                for oarc in transition.output_arcs:
                    write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))
            for index in range(tokens_to_move):
                if iarc.from_place.tokens:
                    token_id = iarc.from_place.tokens.pop(0)
                    tokens_moved += 1
                    write_to_event_log(SIMULATION_TIME, token_id, iarc.from_place.label)  # Log every token movement
        if transition.counter <= len(transition.output_arcs):
            for oarc in transition.output_arcs:
                for index in range(tokens_to_move):
                    new_token = Token()
                    oarc.to_place.tokens.append(new_token.id)
                    write_to_event_log(SIMULATION_TIME, new_token.id, oarc.to_place.label)  # Log new token
                    if index == tokens_to_move - 1 and PROTOCOL:
                        write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
                        write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))

    else:
        for iarc in transition.input_arcs:
            tokens_to_move = min(len(iarc.from_place.tokens), max_tokens_to_transfer)
            if PROTOCOL:  # Log the state before tokens start moving
                write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
                for oarc in transition.output_arcs:
                    write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))
            if transition.Join == 1:
                # Collect token IDs for joined logging
                for _ in range(iarc.multiplicity):
                    if iarc.from_place.tokens:
                        token_id = iarc.from_place.tokens.pop(0)
                        tokens_moved += 1
                transition.counter += 1
                if transition.counter == len(transition.input_arcs):  # Log on last iteration
                    transition.counter = 0
                    for oarc in transition.output_arcs:
                        new_token = Token()
                        oarc.to_place.tokens.append(new_token.id)
                        if PROTOCOL:
                            write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
            else:
                for index in range(tokens_to_move):
                    if iarc.from_place.tokens:
                        token_id = iarc.from_place.tokens.pop(0)
                        tokens_moved += 1
                        for oarc in transition.output_arcs:
                            oarc.to_place.tokens.append(token_id)
                            write_to_event_log(SIMULATION_TIME, token_id, oarc.to_place.label)
                            if index == iarc.multiplicity - 1 and PROTOCOL:
                                write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
                                write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))

    if not transition.input_arcs:
        for oarc in transition.output_arcs:
            tokens_to_move = min(len(oarc.to_place.tokens), max_tokens_to_transfer)
            for index in range(oarc.multiplicity):
                write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))
                new_token = Token()
                oarc.to_place.tokens.append(new_token.id)
                write_to_event_log(SIMULATION_TIME, new_token.id, oarc.to_place.label)
                if index == oarc.multiplicity - 1 and PROTOCOL:
                    write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))  # Log after moving


    # Handle dimension changes
    if transition.dimension_changes:
        for dim_change in transition.dimension_changes:
            dimension, change_type, value = dim_change
            for place in transition.output_arcs:
                if place.to_place.is_tracking and place.to_place.dimension_tracked == dimension:
                    if change_type == "fixed":
                        place.to_place.value += value
                    elif change_type == "rate":
                        calculated_change = value * transition.firing_delay
                        place.to_place.value += calculated_change
                    if PROTOCOL:
                        write_to_protocol(place.to_place.label, SIMULATION_TIME, place.to_place.value)

    # Check if input places are DoT and calculate the duration
    for iarc in transition.input_arcs:
        if iarc.from_place.DoT == 1:
            for entry in tracking_places:
                if entry["place"] == iarc.from_place:
                    duration = SIMULATION_TIME - entry["entrance_time"]
                    # Correctly determine 'value' from dimension_changes
                    for dim_change in transition.dimension_changes:
                        if dim_change[0] == entry["dimension"]:  # Matching the dimension
                            _, _, value = dim_change  # Unpack the tuple to get the value
                            rate_change = duration * value
                            for oarc in transition.output_arcs:
                                if oarc.to_place.dimension_tracked == entry["dimension"]:
                                    oarc.to_place.value += rate_change
                            tracking_places.remove(entry)  # Remove the place info from the tracking list

    # Track again the entrance time and place details for DoT places
    for oarc in transition.output_arcs:
        if oarc.to_place.DoT == 1:
            # Ensure not to add duplicates
            if not any(entry["place"] == oarc.to_place for entry in tracking_places):
                tracking_places.append({
                    "place": oarc.to_place,
                    "dimension": oarc.to_place.dimension_tracked,
                    "entrance_time": SIMULATION_TIME
                })

    # Updating the firing counter and other transition-related statistics only once
    transition.n_times_fired += 1
    transition.time_enabled += transition.firing_delay
    transition.enabled = False




def find_next_firing(spn:SPN)-> Transition:

    total_prob = 0.0
    inc_prob = 0.0
    min_time = 1.0e9
    next_trans = None

    for transition in spn.transitions:
        if transition.enabled == True and transition.t_type == "I":
            total_prob = total_prob + transition.weight
    
    if total_prob > 0:
        min_time = SIMULATION_TIME
        ran = random.uniform(0,total_prob)
        for transition in spn.transitions:
            if transition.enabled == True and transition.t_type == "I":
                inc_prob = inc_prob + transition.weight
                if inc_prob > ran:
                    return transition, min_time
                
    for transition in spn.transitions:
        if transition.enabled == True:
            firing_due_at = transition.enabled_at + transition.firing_delay
            if firing_due_at < min_time:
                min_time = firing_due_at
                next_trans = transition
    return next_trans, min_time

def process_next_event(spn: SPN, max_time):

    global SIMULATION_TIME

    next_transition, min_time = find_next_firing(spn)

    if min_time > max_time:
        SIMULATION_TIME = max_time
        return True
    else:
        SIMULATION_TIME = min_time
    fire_transition(next_transition)

    if VERBOSITY > 1:
        print("\nTransition {} fires at time {}".format(next_transition.label, round(SIMULATION_TIME,2)))

    if VERBOSITY > 2:
        print_marking(spn,SIMULATION_TIME)
    
    found_enabled = update_enabled_flag(spn)
    return found_enabled

def simulate(spn: SPN, max_time=10, start_time=0, time_unit=None, verbosity=2, protocol=True, event_log=True):
    global SIMULATION_TIME, SIMULATION_TIME_UNIT, VERBOSITY, PROTOCOL, tracking_places

    VERBOSITY = verbosity

    if VERBOSITY > 0:
        print("Starting simulation...")
        print("Simulation time limit = {}".format(max_time))

    SIMULATION_TIME = 0
    SIMULATION_TIME_UNIT = time_unit
    PROTOCOL = protocol

    if protocol == True:
        try:
            path = os.path.join(os.getcwd(), "../output/protocols/protocol.csv")
            with open(path, "w", newline="") as protocol:
                writer = csv.writer(protocol)
                writer.writerow(["Place", "Time", "Marking"])
        except:
            with open(os.getcwd() + "../output/protocols/protocol.csv", "w", newline="") as protocol:
                writer = csv.writer(protocol)
                writer.writerow(["Place", "Time", "Marking"])

    if event_log == True:
        try:
            path = os.path.join(os.getcwd(), "../output/event_logs/event_log.csv")
            with open(path, "w", newline="") as event_log:
                writer = csv.writer(event_log)
                writer.writerow(["Time_Stamp", "ID", "Event"])
        except:
            with open(os.getcwd() + "../output/event_logs/event_log.csv", "w", newline="") as event_log:
                writer = csv.writer(event_log)
                writer.writerow(["Time_Stamp", "ID", "Event"])

    initial_marking = get_initial_marking(spn)
    reset_state(spn, initial_marking)

    # Initialize tracking_places with DoT places
    tracking_places = [
        {
            "place": place,
            "dimension": place.dimension_tracked,
            "entrance_time": 0
        }
        for place in spn.places if place.DoT == 1
    ]

    if VERBOSITY > 1:
        print_marking(spn, SIMULATION_TIME)

    ok = update_enabled_flag(spn)

    while SIMULATION_TIME < max_time and ok == True:
        ok = process_next_event(spn, max_time)
        if verbosity > 2:
            print_state(spn, SIMULATION_TIME)

    if ok == False:
        print("No transitions enabled.")

    if VERBOSITY > 0:
        print("\nTime: {}. Simulation terminated.\n".format(SIMULATION_TIME))

    complete_statistics(spn)

    if VERBOSITY > 0:
        print_statistics(spn, SIMULATION_TIME)

    # Calculate input and output values for transitions
    for transition in spn.transitions:
        if transition.input_transition:
            transition.input_value = transition.n_times_fired * transition.capacity
        if transition.output_transition:
            transition.output_value = transition.n_times_fired * transition.capacity

    spn.report_places()
    for transition in spn.transitions:
        if hasattr(transition, 'input_value'):
            print(f"Input value for {transition.label}: {transition.input_value}")
        if hasattr(transition, 'output_value'):
            print(f"Output value for {transition.label}: {transition.output_value}")
