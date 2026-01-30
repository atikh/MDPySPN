import random
import os
import math

from .spn import *
from .spn_io import *
from .RNGFactory import *

SIMULATION_TIME = 0
SIMULATION_TIME_UNIT = None
VERBOSITY = 0
PROTOCOL = False
PROTOCOL = False
SCHEDULE_ITERATOR = 0

# Global list to track places with DoT
tracking_places = []


def marking(place: Place) -> int:
    return len(place.tokens)


def mean_tokens(place: Place) -> float:
    return place.total_tokens / SIMULATION_TIME


def p_not_empty(place: Place) -> float:
    return place.time_non_empty / SIMULATION_TIME


def p_enabled(transition: Transition) -> float:
    return transition.time_enabled / SIMULATION_TIME


def n_firings(transtion: Transition) -> int:
    return transtion.n_times_fired


def throughput(transition: Transition) -> float:
    return transition.n_times_fired / SIMULATION_TIME


def add_tokens(place: Place, n_tokens: int):
    # Assuming `tokens` is a list of token IDs in the Place class

    if PROTOCOL == True:
        # Write the protocol with the ID of the last added token, if any, or 'None'
        last_token_id = place.tokens[-1] if place.tokens else 'None'
        write_to_protocol(place.label, SIMULATION_TIME, len(place.tokens))

    # Update statistics calculations using the current_number_of_tokens instead of place.n_tokens
    place.total_tokens += len(place.tokens) * (SIMULATION_TIME - place.time_changed)
    if len(place.tokens) > 0:
        place.time_non_empty += SIMULATION_TIME - place.time_changed

    place.time_changed = SIMULATION_TIME
    place.n_tokens = len(place.tokens)
    place.n_tokens += n_tokens

    # Handle the addition of new tokens
    for _ in range(n_tokens):
        place.tokens.append(Token())
    place.n_tokens = len(place.tokens)

    if len(place.tokens) > place.max_tokens:
        place.max_tokens = len(place.tokens)

    # Correctly calling write_to_protocol at the end of the function
    if PROTOCOL:
        write_to_protocol(place.label, SIMULATION_TIME, place.n_tokens)


def sub_tokens(place: Place, n_tokens: int):
    if PROTOCOL:
        write_to_protocol(place.label, SIMULATION_TIME, len(place.tokens))

    # stats with current marking
    place.total_tokens += len(place.tokens) * (SIMULATION_TIME - place.time_changed)
    if len(place.tokens) > 0:
        place.time_non_empty += SIMULATION_TIME - place.time_changed
    place.time_changed = SIMULATION_TIME

    # actually remove tokens
    k = min(n_tokens, len(place.tokens))
    for _ in range(k):
        place.tokens.pop(0)   # same policy as your transition logic

    if n_tokens > k:
        print(f"Negative number of tokens in Place {place}")

    place.n_tokens = len(place.tokens)

    if PROTOCOL:
        write_to_protocol(place.label, SIMULATION_TIME, place.n_tokens)



def get_initial_marking(spn: SPN):
    marking = {}
    for place in spn.places:
        place: Place
        # Instead of n_tokens, we store a copy of the current token IDs for each place
        marking[place] = list(place.tokens)  # Assuming `tokens` is a list of token IDs
    return marking


def set_initial_marking(spn: SPN, marking):
    for place in spn.places:
        place.tokens = list(marking[place])
        place.n_tokens = len(place.tokens)


def reset_state(spn: SPN, marking):
    """Reset all places/transitions to a clean state, then restore the initial marking.

    `marking` is expected to be a dict mapping Place -> list_of_tokens
    as returned by get_initial_marking().
    """

    # --- Reset places (CLEAR TOKENS + stats) ---
    for place in spn.places:
        place: Place
        place.tokens = []              # IMPORTANT: clear actual token list
        place.n_tokens = 0             # keep counter consistent
        place.max_tokens = 0 if hasattr(place, "max_tokens") else getattr(place, "max_tokens", 0)

        place.time_changed = 0.0
        place.total_tokens = 0.0
        place.time_non_empty = 0.0

    # --- Reset transitions (counters + clocks + parallel instances) ---
    for transition in spn.transitions:
        transition: Transition
        transition.time_enabled = 0.0
        transition.n_times_fired = 0

        transition.enabled_at = 0.0
        transition.disabled_at = 0.0
        transition.disabled_time = 0.0

        transition.firing_delay = 0.0
        transition.firing_time = 0.0

        transition.clock_active = False
        transition.enabled = False

        # Clear any pending per-token timers
        if hasattr(transition, "pt_instances"):
            transition.pt_instances = []
            transition.pt_busy_until = 0.0

        # Reset any join/fork counters used by existing logic
        if hasattr(transition, "counter"):
            transition.counter = 0

        # Reset reset-policy fields if they exist in your model
        if hasattr(transition, "reset_time"):
            transition.reset_time = 0.0

    # --- Restore initial marking (tokens list per place) ---
    for place in spn.places:
        place: Place
        place.tokens = list(marking.get(place, []))
        place.n_tokens = len(place.tokens)
        if hasattr(place, "max_tokens"):
            place.max_tokens = max(place.max_tokens, place.n_tokens)


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
            transition.firing_delay = round(transition.handicap, 2) * transition.firing_delay
        elif transition.handicap_type == "decrease":
            transition.firing_delay = transition.firing_delay / round(transition.handicap, 2)

    if transition.t_type == "T" and SIMULATION_TIME_UNIT != None:
        transition.firing_delay = convert_delay(transition.firing_delay, time_unit=transition.time_unit,
                                                simulation_time_unit=SIMULATION_TIME_UNIT)

    transition.firing_time = transition.enabled_at + transition.firing_delay

def sample_firing_delay(transition: Transition) -> float:
    """Sample a delay without overwriting the transition's single-clock fields."""
    if transition.t_type != "T":
        return 0.0

    dist = list(transition.distribution.keys())[0]
    parameters = list(transition.distribution[dist].values())

    match dist:
        case "det":
            delay = get_delay("det", parameters[0])
        case "uniform":
            delay = get_delay("uniform", parameters[0], parameters[1])
        case "expon":
            delay = get_delay("expon", parameters[0], parameters[1])
        case "norm":
            delay = get_delay("norm", parameters[0], parameters[1])
        case "lognorm":
            delay = get_delay("lognorm", parameters[0], parameters[1], parameters[2])
        case "triang":
            delay = get_delay("triang", parameters[0], parameters[1], parameters[2])
        case "cauchy":
            delay = get_delay("cauchy", parameters[0], parameters[1])
        case "exponpow":
            delay = get_delay("exponpow", parameters[0], parameters[1], parameters[2])
        case "gamma":
            delay = get_delay("gamma", parameters[0], parameters[1], parameters[2])
        case "weibull_min":
            delay = get_delay("weibull_min", parameters[0], parameters[1], parameters[2])
        case _:
            raise Exception("Distribution undefined for transition {}".format(transition))

    if transition.handicap != 1:
        if transition.handicap_type == "increase":
            delay = round(transition.handicap, 2) * delay
        elif transition.handicap_type == "decrease":
            delay = delay / round(transition.handicap, 2)

    if transition.t_type == "T" and SIMULATION_TIME_UNIT is not None:
        delay = convert_delay(delay, time_unit=transition.time_unit, simulation_time_unit=SIMULATION_TIME_UNIT)

    return delay

def set_reset_time(transition: Transition):
    transition.reset_time = transition.enabled_at + transition.reset_threshold


def convert_delay(delay, time_unit=None, simulation_time_unit=None):
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
def start_parallel_instances(transition: Transition):
    """Start as many independent instances as possible right now.

    Minimal safe semantics:
      - timed transitions only
      - exactly 1 input arc
      - not Join/Fork
      - reserves tokens immediately (removes them from input place)
    """
    if getattr(transition, "parallel_timing", False) != True:
        return
    if transition.t_type != "T":
        return

    if not hasattr(transition, "pt_instances") or transition.pt_instances is None:
        transition.pt_instances = []

    if transition.Join == 1:
        raise Exception(
            "parallel_timing only implemented for transitions with exactly 1 input arc (no Join): {}".format(
                transition.label
            )
        )
    if len(transition.input_arcs) != 1:
        raise Exception("parallel_timing currently requires exactly 1 input arc: {}".format(transition.label))

    iarc = transition.input_arcs[0]

    while is_enabled(transition) == True:
        if len(iarc.from_place.tokens) < iarc.multiplicity:
            break

        # Reserve tokens NOW (so they cannot be taken by other transitions).
        reserved = []
        for _ in range(iarc.multiplicity):
            reserved.append(iarc.from_place.tokens.pop(0))

        delay = sample_firing_delay(transition)
        finish_time = SIMULATION_TIME + delay
        base = max(getattr(transition, "pt_busy_until", SIMULATION_TIME), SIMULATION_TIME)
        busy_time = max(0.0, finish_time - base)
        transition.pt_busy_until = max(base, finish_time)

        transition.pt_instances.append({
            "fire_time": finish_time,
            "delay": delay,
            "busy_time": busy_time,
            "tokens": reserved,
        })


def fire_parallel_instance(transition: Transition, spn: SPN, instance: dict):
    """Complete one scheduled instance: move reserved tokens to outputs + apply dimension impacts."""
    if not hasattr(transition, "pt_instances") or transition.pt_instances is None:
        transition.pt_instances = []

    try:
        transition.pt_instances.remove(instance)
    except:
        pass

    delay = instance.get("delay", 0.0)
    tokens = instance.get("tokens", [])

    # 1) Move tokens to outputs and write event log (same style as your existing fire_transition)
    for tok in tokens:
        # Move reserved tokens to outputs
        if transition.output_arcs:

            # Fork: first produced token uses the reserved entity token,
            # remaining produced tokens are NEW tokens
            if transition.Fork == 1:
                entity_token = tokens[0] if tokens else Token()
                used_entity = False

                for oarc in transition.output_arcs:
                    for _ in range(oarc.multiplicity):
                        if not used_entity:
                            produced = entity_token
                            used_entity = True
                        else:
                            produced = Token()

                        oarc.to_place.tokens.append(produced)
                        oarc.to_place.n_tokens = len(oarc.to_place.tokens)
                        write_to_event_log(SIMULATION_TIME, produced.id, transition.label, transition, spn)

            # Non-fork: keep your old behavior (move token to outputs)
            else:
                for tok in tokens:
                    for oarc in transition.output_arcs:
                        oarc.to_place.tokens.append(tok)
                        oarc.to_place.n_tokens = len(oarc.to_place.tokens)
                    write_to_event_log(SIMULATION_TIME, tok.id, transition.label, transition, spn)

        else:
            # No outputs: still log the event(s)
            for tok in tokens:
                write_to_event_log(SIMULATION_TIME, tok.id, transition.label, transition, spn)

    # 2) Apply dimension changes (copy of your logic, but using instance delay)
    if transition.dimension_changes:
        for dimension, change_type, value in transition.dimension_changes:
            if dimension not in transition.dimension_table:
                transition.dimension_table[dimension] = 0.0

            if change_type == "fixed":
                transition.dimension_table[dimension] += value

            elif change_type == "rate":
                eff = float(instance.get("busy_time", delay))
                transition.dimension_table[dimension] += value * eff

    # 3) Update stats (same counters as a normal firing)
    transition.n_times_fired += 1
    transition.time_enabled += delay
    transition.enabled = False


def update_enabled_flag(spn: SPN):
    """Updates enabled flags.
    If a timed transition has parallel_timing=True, start per-token instances and keep simulation alive while pending.
    """
    found_enabled = False

    # 0) Start new parallel instances first (so timers exist even if transition itself isn't 'enabled' later)
    for transition in spn.transitions:
        if getattr(transition, "parallel_timing", False) == True and transition.t_type == "T":
            start_parallel_instances(transition)
            transition.enabled = is_enabled(transition)  # can start another instance now?
            if transition.enabled or (hasattr(transition, "pt_instances") and len(transition.pt_instances) > 0):
                found_enabled = True

    # 1) Original disable logic for non-parallel transitions
    for transition in spn.transitions:
        if getattr(transition, "parallel_timing", False) == True and transition.t_type == "T":
            continue

        if is_enabled(transition) == False:
            if transition.enabled == True and transition.memory_policy == "AGE":
                transition.disabled_at = SIMULATION_TIME
                transition.clock_active = True
            transition.enabled = False

    # 2) Original enable logic for non-parallel transitions
    for transition in spn.transitions:
        if getattr(transition, "parallel_timing", False) == True and transition.t_type == "T":
            continue

        if is_enabled(transition) == True:
            if transition.enabled == False:
                if transition.clock_active == True:
                    transition.disabled_time += SIMULATION_TIME - transition.disabled_at
                else:
                    set_firing_time(transition)
            transition.enabled = True
            found_enabled = True

    return found_enabled

def dot_full_init(place: Place):
    """
    Initialize FULL-idle tracking for a DoT place.

    FULL means: len(place.tokens) == place.dot_full_marking (the initial marking).
    """
    if getattr(place, "DoT", 0) != 1:
        return
    if getattr(place, "dimension_tracked", None) is None:
        return

    # store initial marking once
    if not hasattr(place, "dot_full_marking"):
        place.dot_full_marking = len(place.tokens)

    place.dot_full_active = (len(place.tokens) == place.dot_full_marking and place.dot_full_marking > 0)
    place.dot_full_start = SIMULATION_TIME if place.dot_full_active else None


def dot_full_on_remove(place: Place, transition: Transition):
    """
    Call this RIGHT BEFORE removing a token from `place`.
    If the place is FULL, we close the FULL interval and add its duration to transition.dimension_table[dimension_tracked].
    """
    if getattr(place, "DoT", 0) != 1:
        return
    dim = getattr(place, "dimension_tracked", None)
    if dim is None:
        return
    if not hasattr(place, "dot_full_marking"):
        place.dot_full_marking = len(place.tokens)

    # leaving FULL state now?
    if getattr(place, "dot_full_active", False) and len(place.tokens) == place.dot_full_marking:
        start = getattr(place, "dot_full_start", None)
        if start is not None:
            dur = SIMULATION_TIME - start
            if dur > 0:
                transition.dimension_table[dim] = transition.dimension_table.get(dim, 0.0) + dur

        place.dot_full_active = False
        place.dot_full_start = None


def dot_full_on_add(place: Place):
    """
    Call this RIGHT AFTER adding a token to `place`.
    If we just reached FULL, start a new FULL interval.
    """
    if getattr(place, "DoT", 0) != 1:
        return
    if getattr(place, "dimension_tracked", None) is None:
        return
    if not hasattr(place, "dot_full_marking"):
        place.dot_full_marking = len(place.tokens)

    # entering FULL state now?
    if (not getattr(place, "dot_full_active", False)) and len(place.tokens) == place.dot_full_marking and place.dot_full_marking > 0:
        place.dot_full_active = True
        place.dot_full_start = SIMULATION_TIME


def fire_transition(transition: Transition, spn: SPN):
    """Fires a transition, moves tokens, and updates dimension tables.

    IMPORTANT:
      - Token consumption/production happens ONLY ONCE in this function.
      - Fork policy matches PySPN:
          * consume entity token from input
          * first produced output token uses entity token
          * all additional produced output tokens are NEW tokens
    """
    global tracking_places
    for iarc in transition.input_arcs:
        iarc.from_place.n_tokens = len(iarc.from_place.tokens)
    for oarc in transition.output_arcs:
        oarc.to_place.n_tokens = len(oarc.to_place.tokens)

    # Protocol pre-log
    if PROTOCOL:
        for iarc in transition.input_arcs:
            write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
        for oarc in transition.output_arcs:
            write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))

    # Capacity: interpret as max number of "entity tokens" processed per firing (default: unlimited)
    max_tokens_to_transfer = transition.capacity if transition.capacity is not None else float("inf")
    remaining_cap = max_tokens_to_transfer

    # ADDED: count how many entity-units we actually processed in THIS fire()
    # (so rate impacts can be scaled correctly)
    entities_processed = 0

    # --------------------------
    # 1) Source transitions (no inputs): create tokens once
    # --------------------------
    if not transition.input_arcs:
        for oarc in transition.output_arcs:
            for _ in range(oarc.multiplicity):
                if remaining_cap <= 0:
                    break
                t = Token()
                oarc.to_place.tokens.append(t)
                oarc.to_place.n_tokens = len(oarc.to_place.tokens)
                write_to_event_log(SIMULATION_TIME, t.id, transition.label, transition, spn)
                remaining_cap -= 1
                entities_processed += 1  # ADDED

        # DoT output tracking (keep your existing tracking approach)
        for oarc in transition.output_arcs:
            output_place = oarc.to_place
            if output_place.DoT == 1:
                existing_entry = next((e for e in tracking_places if e["place"] == output_place), None)
                if not existing_entry:
                    tracking_places.append({
                        "place": output_place,
                        "dimension": output_place.dimension_tracked,
                        "entrance_time": SIMULATION_TIME
                    })
                else:
                    existing_entry["entrance_time"] = SIMULATION_TIME

        transition.n_times_fired += 1
        transition.time_enabled += transition.firing_delay
        transition.enabled = False

        # IMPORTANT: apply dimension_changes here too (otherwise sources never add rate impacts)
        if transition.dimension_changes:
            for dimension, change_type, value in transition.dimension_changes:
                if dimension not in transition.dimension_table:
                    transition.dimension_table[dimension] = 0.0

                if change_type == "fixed":
                    transition.dimension_table[dimension] += value
                elif change_type == "rate":
                    def fix_fraction2(x: float) -> float:
                        m = math.floor(x)
                        frac_hundred = math.floor((x - m) * 100)
                        if frac_hundred >= 60:
                            frac_hundred -= 60
                        return m + frac_hundred / 100.0

                    transition.dimension_table[dimension] += value * fix_fraction2(transition.firing_delay) * max(1,
                                                                                                                  entities_processed)

        if PROTOCOL:
            for oarc in transition.output_arcs:
                write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))
        return

    # --------------------------
    # 2) Join: consume from each input arc, produce ONE token
    # --------------------------
    if transition.Join == 1:
        if remaining_cap <= 0:
            transition.enabled = False
            return

        collected = []  # (place, token)
        for iarc in transition.input_arcs:
            for _ in range(iarc.multiplicity):
                if not iarc.from_place.tokens:
                    raise RuntimeError(
                        f"Join transition {transition.label} fired but {iarc.from_place.label} lacks tokens."
                    )
                tok = iarc.from_place.tokens.pop(0)
                collected.append((iarc.from_place, tok))
            iarc.from_place.n_tokens = len(iarc.from_place.tokens)

        # Preserve one token from a "normal" place (DoT != 1) if any; else create a new token
        preserved = None
        for place, tok in collected:
            if place.DoT != 1:
                preserved = tok
                break
        new_tok = preserved if preserved is not None else Token()

        for oarc in transition.output_arcs:
            for _ in range(oarc.multiplicity):
                oarc.to_place.tokens.append(new_tok)
                oarc.to_place.n_tokens = len(oarc.to_place.tokens)

        nid = new_tok.id if hasattr(new_tok, "id") else new_tok
        write_to_event_log(SIMULATION_TIME, nid, transition.label, transition, spn)

        remaining_cap -= 1
        entities_processed += 1  # ADDED

    # --------------------------
    # 3) Fork: entity token goes to first produced output token, others are NEW tokens
    # --------------------------
    elif transition.Fork == 1:
        if remaining_cap <= 0:
            transition.enabled = False
            return

        if len(transition.input_arcs) != 1:
            raise RuntimeError(
                f"Fork transition {transition.label} expects exactly 1 input arc in this implementation.")

        iarc = transition.input_arcs[0]

        # consume multiplicity (usually 1)
        consumed = []
        for _ in range(iarc.multiplicity):
            if not iarc.from_place.tokens:
                raise RuntimeError(
                    f"Fork transition {transition.label} fired but {iarc.from_place.label} lacks tokens."
                )
            consumed.append(iarc.from_place.tokens.pop(0))
        iarc.from_place.n_tokens = len(iarc.from_place.tokens)

        entity_token = consumed[0] if consumed else Token()

        used_entity = False
        for oarc in transition.output_arcs:
            for _ in range(oarc.multiplicity):
                if not used_entity:
                    oarc.to_place.tokens.append(entity_token)
                    write_to_event_log(SIMULATION_TIME, entity_token.id, transition.label, transition, spn)
                    used_entity = True
                else:
                    t = Token()
                    oarc.to_place.tokens.append(t)
                    write_to_event_log(SIMULATION_TIME, t.id, transition.label, transition, spn)

                oarc.to_place.n_tokens = len(oarc.to_place.tokens)

        remaining_cap -= 1
        entities_processed += 1  # ADDED

    # --------------------------
    # 4) Normal: move consumed token(s) to outputs (same token identity)
    # --------------------------
    else:
        for iarc in transition.input_arcs:
            # each "entity" here consumes iarc.multiplicity tokens
            while remaining_cap > 0:
                # if not enough tokens to consume multiplicity, stop
                if len(iarc.from_place.tokens) < iarc.multiplicity:
                    break

                consumed = []
                for _ in range(iarc.multiplicity):
                    consumed.append(iarc.from_place.tokens.pop(0))

                iarc.from_place.n_tokens = len(iarc.from_place.tokens)

                tok = consumed[0]  # entity token identity

                for oarc in transition.output_arcs:
                    for __ in range(oarc.multiplicity):
                        oarc.to_place.tokens.append(tok)
                        oarc.to_place.n_tokens = len(oarc.to_place.tokens)

                tid = tok.id if hasattr(tok, "id") else tok
                write_to_event_log(SIMULATION_TIME, tid, transition.label, transition, spn)

                remaining_cap -= 1
                entities_processed += 1  # ADDED

    # --------------------------
    # ---- KEEP YOUR MULTI-DIMENSION / DoT LOGIC BELOW (unchanged) ----
    # --------------------------

    # Track the entrance time and place details for DoT places
    for oarc in transition.output_arcs:
        if oarc.to_place.DoT == 1:
            for iarc in transition.input_arcs:
                dimension = iarc.from_place.dimension_tracked
                duration = SIMULATION_TIME - iarc.from_place.time_entered

                if dimension in transition.dimension_table:
                    transition.dimension_table[dimension] += duration
                else:
                    transition.dimension_table[dimension] = duration

                iarc.from_place.time_entered = SIMULATION_TIME

    # Handle dimension changes
    if transition.dimension_changes:
        for dimension, change_type, value in transition.dimension_changes:
            if dimension not in transition.dimension_table:
                transition.dimension_table[dimension] = 0.0

            if change_type == "fixed":
                transition.dimension_table[dimension] += value

            elif change_type == "rate":
                # ADDED: scale by how many entity-units were actually processed in this fire()
                transition.dimension_table[dimension] += value * transition.firing_delay 

    # Check if input places are DoT and calculate the duration
    for iarc in transition.input_arcs:
        input_place = iarc.from_place
        if input_place.DoT == 1:
            tracking_entry = next((entry for entry in tracking_places if entry["place"] == input_place), None)
            if tracking_entry:
                duration = SIMULATION_TIME - tracking_entry["entrance_time"]
                tracked_dimension = tracking_entry["dimension"]

                for dimension, change_type, value in transition.dimension_changes:
                    if dimension == tracked_dimension and change_type == "rate":
                        if dimension in transition.dimension_table:
                            transition.dimension_table[dimension] += duration * value

                tracking_places.remove(tracking_entry)

    # Track again the entrance time and place details for DoT places
    for oarc in transition.output_arcs:
        output_place = oarc.to_place
        if output_place.DoT == 1:
            existing_entry = next((entry for entry in tracking_places if entry["place"] == output_place), None)
            if not existing_entry:
                tracking_places.append({
                    "place": output_place,
                    "dimension": output_place.dimension_tracked,
                    "entrance_time": SIMULATION_TIME
                })
            else:
                existing_entry["entrance_time"] = SIMULATION_TIME

    # Protocol post-log
    if PROTOCOL:
        for iarc in transition.input_arcs:
            write_to_protocol(iarc.from_place.label, SIMULATION_TIME, len(iarc.from_place.tokens))
        for oarc in transition.output_arcs:
            write_to_protocol(oarc.to_place.label, SIMULATION_TIME, len(oarc.to_place.tokens))

    transition.n_times_fired += 1
    transition.time_enabled += transition.firing_delay
    transition.enabled = False



def find_next_firing(spn: SPN):
    total_prob = 0.0
    inc_prob = 0.0
    min_time = 1.0e9
    next_trans = None
    next_instance = None

    # 1) Immediate transitions (unchanged)
    for transition in spn.transitions:
        if transition.enabled == True and transition.t_type == "I":
            total_prob = total_prob + transition.weight

    if total_prob > 0:
        min_time = SIMULATION_TIME
        ran = random.uniform(0, total_prob)
        for transition in spn.transitions:
            if transition.enabled == True and transition.t_type == "I":
                inc_prob = inc_prob + transition.weight
                if inc_prob > ran:
                    return transition, min_time, None

    # 2) Parallel instance events
    for transition in spn.transitions:
        if getattr(transition, "parallel_timing", False) == True and transition.t_type == "T":
            if hasattr(transition, "pt_instances") and transition.pt_instances and len(transition.pt_instances) > 0:
                inst = min(transition.pt_instances, key=lambda x: x["fire_time"])
                if inst["fire_time"] < min_time:
                    min_time = inst["fire_time"]
                    next_trans = transition
                    next_instance = inst

    # 3) Regular timed transitions (unchanged)
    for transition in spn.transitions:
        if getattr(transition, "parallel_timing", False) == True and transition.t_type == "T":
            continue

        if transition.enabled == True:
            firing_due_at = transition.enabled_at + transition.firing_delay
            if firing_due_at < min_time:
                min_time = firing_due_at
                next_trans = transition
                next_instance = None

    return next_trans, min_time, next_instance



def process_next_event(spn: SPN, max_time):
    global SIMULATION_TIME

    next_transition, min_time, next_instance = find_next_firing(spn)

    if min_time > max_time:
        SIMULATION_TIME = max_time
        return True
    else:
        SIMULATION_TIME = min_time

    if next_instance is not None and getattr(next_transition, "parallel_timing", False) == True:
        fire_parallel_instance(next_transition, spn, next_instance)
    else:
        fire_transition(next_transition, spn)

    if VERBOSITY > 1:
        print("\nTransition {} fires at time {}".format(next_transition.label, round(SIMULATION_TIME, 2)))

    if VERBOSITY > 2:
        print_marking(spn, SIMULATION_TIME)

    found_enabled = update_enabled_flag(spn)
    return found_enabled



def simulate(spn: SPN, max_time=10, start_time=0, time_unit=None, verbosity=2, protocol=True, event_log=True,
             Dimensions=None):
    print("Simulation starts", Dimensions)

    global SIMULATION_TIME, SIMULATION_TIME_UNIT, VERBOSITY, PROTOCOL, tracking_places

    VERBOSITY = verbosity
    spn.simulation_time = max_time  # Store max_time in the SPN object

    if VERBOSITY > 0:
        print("Starting simulation...")
        print(f"Simulation time limit = {spn.simulation_time}")

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
            dimension_headers = [f"{dim.capitalize()} _Stamp" for dim in Dimensions if dim != "time"]
            headers = ["Time_Stamp", "ID"] + dimension_headers + ["Event"]

            with open(path, "w", newline="") as event_log:
                writer = csv.writer(event_log)
                writer.writerow(headers)
        except Exception as e:
            print(f"Error initializing event log file: {e}")

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

    for place in spn.places:
        dot_full_init(place)

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
            transition.input_value = transition.n_times_fired
        if transition.output_transition:
            transition.output_value = transition.n_times_fired

    for transition in spn.transitions:
        if hasattr(transition, 'input_value'):
            print(f"Input value for {transition.label}: {transition.input_value}")
        if hasattr(transition, 'output_value'):
            print(f"Output value for {transition.label}: {transition.output_value}")
    dimension_totals = {}

    # Sum dimensions from transitions
    for transition in spn.transitions:
        if hasattr(transition, "dimension_table") and transition.dimension_table:
            for dimension, value in transition.dimension_table.items():
                dimension_totals[dimension] = dimension_totals.get(dimension, 0) + value

    #  Print Final Summary of All Dimensions
    print("\nSummary of Dimensions:")
    for dimension, total in dimension_totals.items():
        if dimension is not None:  # Ensure None values are excluded
            print(f"{dimension}: {total:.2f}")
    print("Simulation ends")

    ############################
    ####WRITE KPIs#############
    ############################
    try:
        dims_source = Dimensions if Dimensions else getattr(spn, "dimensions", None)
        if dims_source:
            dims_order = [d for d in dims_source if d not in (None, "time")]
        else:
            dims_order = [d for d in dimension_totals.keys() if d not in (None, "time")]
    except Exception:
        dims_order = [d for d in dimension_totals.keys() if d not in (None, "time")]

    # Check if there is ANY input/output transition info at all
    has_input = any(getattr(t, "input_transition", False) or hasattr(t, "input_value") for t in spn.transitions)
    has_output = any(getattr(t, "output_transition", False) or hasattr(t, "output_value") for t in spn.transitions)

    header = ["Time_Stamp"]
    row = [round(SIMULATION_TIME, 2)]

    # Only calculate/write Inputs, Outputs, Throughput if at least one exists
    if has_input or has_output:
        # Detect transitions that actually have input/output values (same logic as your print loop)
        input_transitions = [t for t in spn.transitions if hasattr(t, "input_value")]
        output_transitions = [t for t in spn.transitions if hasattr(t, "output_value")]

        has_input = len(input_transitions) > 0
        has_output = len(output_transitions) > 0

        header = ["Time_Stamp"]
        row = [round(SIMULATION_TIME, 2)]

        # Only calculate/write these 3 if we have ANY input/output transitions
        if has_input or has_output:
            if has_input:
                Inputt = sum(float(getattr(t, "input_value", 0) or 0) for t in input_transitions)
                header.append("Inputs")
                row.append(round(Inputt, 2))

            if has_output:
                Ouputt = sum(float(getattr(t, "output_value", 0) or 0) for t in output_transitions)
                header.append("Outputs")
                row.append(round(Ouputt, 2))

            # Throughput only if both exist and Inputs != 0
            if has_input and has_output:
                Throughputt = (Ouputt / Inputt) if Inputt != 0 else 0.0
                header.append("Throughput")
                row.append(round(Throughputt, 2))

        # Always write dimensions
        header += dims_order
        row += [round(float(dimension_totals.get(d, 0.0)), 2) for d in dims_order]

        write_kpis_to_csv(row, path="../output/KPI/kpi.csv", header=header)
        # -----------------------------
        # NEW: KPIs per activity (each transition's dimension_table)
        # -----------------------------
        per_act_header = ["Time_Stamp"]
        per_act_row = [round(SIMULATION_TIME, 2)]

        for t in spn.transitions:
            if hasattr(t, "dimension_table") and t.dimension_table:
                for dim in sorted([d for d in t.dimension_table.keys() if d is not None]):
                    per_act_header.append(f"{t.label}__{dim}")
                    per_act_row.append(round(float(t.dimension_table.get(dim, 0.0) or 0.0), 2))

        write_kpis_to_csv(
            per_act_row,
            path="../output/KPI/KPIs_per_activitiy.csv",
            header=per_act_header
        )


def write_kpis_to_csv(data, path="../output/KPI/kpi.csv", header=None):
    import csv
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)

    # If file exists and header changed, rewrite file with the new header and pad old rows
    if header is not None and os.path.exists(path) and os.stat(path).st_size > 0:
        with open(path, "r", newline="") as f:
            reader = csv.reader(f)
            existing_header = next(reader, None)
            existing_rows = list(reader)

        if existing_header != header:
            fixed_rows = []
            for r in existing_rows:
                if len(r) < len(header):
                    r = r + [""] * (len(header) - len(r))
                elif len(r) > len(header):
                    r = r[:len(header)]
                fixed_rows.append(r)

            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(fixed_rows)

    # Write header only if file is empty/new
    write_header = header is not None and (not os.path.exists(path) or os.stat(path).st_size == 0)

    with open(path, "a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(header)
        writer.writerow(data)
