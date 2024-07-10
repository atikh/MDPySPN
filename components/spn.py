from __future__ import annotations
import uuid
import importlib
class SPN(object):
    def __init__(self):
        # Dynamically import Total_Dimensions from Main.py
        main_module = importlib.import_module("Main")
        self.dimensions = getattr(main_module, 'Total_Dimensions', None)
        self.places = []
        self.transitions = []

    def add_place(self, place):
        self.places.append(place)

    def add_transition(self, transition):
        self.transitions.append(transition)

    def add_input_arc(self, place, transition, multiplicity=1):
        arc = InputArc()
        arc.from_place = place
        arc.to_transition = transition
        arc.multiplicity = multiplicity
        transition.input_arcs.append(arc)
        place.input_arcs.append(arc)

    def add_output_arc(self, transition, place, multiplicity=1):
        arc = OutputArc()
        arc.from_transition = transition
        arc.to_place = place
        arc.multiplicity = multiplicity
        transition.output_arcs.append(arc)
        place.output_arcs.append(arc)

    def add_inhibitor_arc(self, transition, place, multiplicity=1):
        arc = InhibitorArc()
        arc.to_transition = transition
        arc.from_place = place
        arc.multiplicity = multiplicity
        transition.inhibitor_arcs.append(arc)
        place.inhibitor_arcs.append(arc)

    def get_place_by_label(self, label):
        for place in self.places:
            if place.label == label:
                return place
        print("No place found with specified label.")
        return None

    def get_transition_by_label(self, label):
        for transition in self.transitions:
            if transition.label == label:
                return transition
        print("No transition found with specified label.")
        return None

    def get_arrival_transitions(self):
        arrival_transitions = []
        for transition in self.transitions:
            if not transition.input_arcs:
                arrival_transitions.append(transition)
        return arrival_transitions

    def summarize_dimensions(self):
        dimension_totals = {}
        for place in self.places:
            if place.is_dimension_holder:
                dim = place.dimension_tracked
                if dim in dimension_totals:
                    dimension_totals[dim] += place.get_value()
                else:
                    dimension_totals[dim] = place.get_value()
        return dimension_totals

    def print_dimension_summary(self):
        totals = self.summarize_dimensions()
        for dimension, total in totals.items():
            print(f"Total {dimension}: {total}")

    def report_places(self):
        dimension_totals = {}
        print("Current Status of Places:")
        for place in self.places:
            print(place)  # This will use the __str__ method of Place class
            if place.is_dimension_holder and place.dimension_tracked:
                if place.dimension_tracked not in dimension_totals:
                    dimension_totals[place.dimension_tracked] = place.value
                else:
                    dimension_totals[place.dimension_tracked] += place.value

        print("\nSummary of Dimensions:")
        for dimension, total in dimension_totals.items():
            print(f"Total {dimension}: {total}")
        

class Place:
    def __init__(self, label: str, n_tokens: int = 0, is_dimension_holder=False, dimension_tracked=None, initial_value=None, DoT=None):
        self.label = label
        self.n_tokens = n_tokens
        self.is_dimension_holder = is_dimension_holder
        self.dimension_tracked = dimension_tracked
        self.value = initial_value if initial_value is not None else 0.0  # Ensure value is initialized
        self.DoT = DoT
        self.tokens = []

        if not is_dimension_holder:
            for _ in range(n_tokens):
                self.tokens.append(Token())

        self.max_tokens = 0
        self.time_changed = 0
        self.total_tokens = 0
        self.time_non_empty = 0

        self.input_arcs = []
        self.output_arcs = []
        self.inhibitor_arcs = []

    def set_tokens(self, n_tokens: int):
        current_tokens = len(self.tokens)
        if n_tokens > current_tokens:
            self.tokens.extend([Token() for _ in range(n_tokens - current_tokens)])
        elif n_tokens < current_tokens:
            self.tokens = self.tokens[:n_tokens]

    def __str__(self):
        if self.is_dimension_holder:
            return f"Place {self.label}: {self.dimension_tracked} = {self.value}"
        else:
            return f"Place {self.label}: Tokens = {len(self.tokens)}"

    def set_value(self, value):
        if self.is_dimension_holder:
            self.value = value
        else:
            raise ValueError("This place is not a dimension holder.")

    def get_value(self):
        if self.is_dimension_holder:
            return self.value
        else:
            raise ValueError("This place is not a dimension holder.")


class Transition(object):

    def __init__(self, label: str, t_type: str, Join=0, Fork=0, dimension_changes=None, **kwargs):
        self.label = label
        self.t_type = t_type
        self.dimension_changes = dimension_changes or []  # Always initialize dimension_changes


        if self.t_type == "T":
            self.distribution = None
            self.time_unit = None
        elif self.t_type == "I":
            self.weight = 1
        else: raise Exception("Not a valid transition type.")

        self.handicap = 1 #Handicap for experiments with new configurations; Handicap will influence firing times of transition; <1 -> transition fill fire faster; >1 -> transition will fire slower
        self.handicap_type = None
        self.allow_reset = False
        self.reset_threshold = 0 #Threshold; can be used e.g., for testing preventive maintenance with equipment failure transitions
        self.reset_time = 0

        self.guard_function = None
        self.memory_policy = "ENABLE"
        self.clock_active = False

        self.enabled = False
        self.enabled_at = 0
        self.disabled_at = 0
        self.disabled_time = 0
        self.firing_delay = 0
        self.firing_time = 0

        self.time_enabled = 0
        self.n_times_fired = 0

        self.input_arcs = []
        self.output_arcs = []
        self.inhibitor_arcs = []

        self.counter = 0
        self.Join = Join
        self.Fork=Fork


    def set_distribution(self, distribution, a=0.0, b=0.0, c=0.0, d=0.0, time_unit:str = None):
        if self.t_type == "T":
            self.distribution = {distribution:{"a":a,"b":b,"c":c,"d":d}}
            self.time_unit = time_unit
        else: raise Exception("Can not set distribution for immediate transition.")
    
    def set_weight(self, weight: float):
        if self.t_type == "I":
            self.weight = weight
        else: raise Exception("Can not set weight for timed transition.")

    def set_guard_function(self, guard_function):
        self.guard_function = guard_function

    def set_memory_policy(self, type):
        self.memory_policy = type

    def add_dimension_change(self, dimension, change_type, value):
        self.dimension_changes.append((dimension, change_type, value))

class InputArc(object):
    def __init__(self):
        self.to_transition = None
        self.from_place = None
        self.multiplicity = 0

class InhibitorArc(object):
    def __init__(self):
        self.to_transition = None
        self.from_place = None
        self.multiplicity = 0

class OutputArc(object):
    def __init__(self):
        self.to_place = None
        self.from_transition = None
        self.multiplicity = 0


# Hypothetical Token class implementation
class Token:
    _id_counter = 0

    def __init__(self):
        type(self)._id_counter += 1
        self.id = type(self)._id_counter

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"Token({self.id})"
