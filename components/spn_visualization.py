from .spn import *
from graphviz import Digraph

def format_label(value):
    # Convert the float to a string with two decimal precision
    value_str = f"{value:.2f}"
    # Check if the string length exceeds 6 characters (including decimal point and two decimal places)
    if len(value_str) > 9:
        # Return the string truncated to 4 characters plus ellipsis
        return value_str[:6] + "..."
    return value_str

def draw_spn(spn, file="spn_default", show=True, print_place_labels=False, rankdir="TB"):
    spn_graph = Digraph(engine="dot", graph_attr={'rankdir': rankdir})

    # Prepare the dimension summary text
    dimension_summary = "Summary of Dimensions:\n"
    dimension_totals = {}
    for place in spn.places:
        if place.is_dimension_holder:
            if place.dimension_tracked not in dimension_totals:
                dimension_totals[place.dimension_tracked] = place.value
            else:
                dimension_totals[place.dimension_tracked] += place.value

    for dim, value in dimension_totals.items():
        dimension_summary += f"{dim}: {value:.2f}\n"  # Format value to 2 decimal places

    # Add input and output values for transitions
    input_output_summary = "Input/Output Summary:\n"
    for transition in spn.transitions:
        if hasattr(transition, 'input_value'):
            input_output_summary += f"{transition.label} input: {transition.input_value}\n"
        if hasattr(transition, 'output_value'):
            input_output_summary += f"{transition.label} output: {transition.output_value}\n"

    summary_text = dimension_summary + "\n" + input_output_summary

    # Add a text box at the top left of the diagram for the summary with a gray background
    spn_graph.attr('node', shape='plaintext', style='filled', fillcolor='lightgrey')
    spn_graph.node('summary', label=summary_text)
    spn_graph.attr('node', shape='ellipse', style='', fillcolor='')

    # Draw places and marking
    for place in spn.places:
        token_count = len(place.tokens)  # Get the count of tokens from the tokens list

        if place.is_dimension_holder:
            formatted_value = format_label(place.value)
            dimension_label = place.dimension_tracked
            spn_graph.node(place.label, label=formatted_value, shape="circle", style='', fontsize='8', width='0.6',
                           fixedsize='true', xlabel=dimension_label)
        else:
            if token_count == 0:
                label = "" if not print_place_labels else place.label
                spn_graph.node(place.label, shape="circle", label=label,
                               xlabel=place.label if print_place_labels else "", height="0.6", width="0.6",
                               fixedsize='true')
            else:
                if token_count < 5:
                    lb = "<"
                    for token_number in range(1, token_count + 1):
                        lb += "&#9679;"
                        if token_number % 2 == 0:
                            lb += "<br/>"
                    lb += ">"
                else:
                    lb = f"{token_count}"
                label = lb if not print_place_labels else ""
                spn_graph.node(place.label, shape='circle', label=label,
                               xlabel=place.label if print_place_labels else "", height='0.6', width='0.6',
                               fixedsize='true')

    # Draw transitions with external labels
    for transition in spn.transitions:
        if transition.t_type == "T":
            if rankdir == "TB":
                spn_graph.node(transition.label, shape='rectangle', label='', width='0.6', height='0.2',
                               fixedsize='true', xlabel=transition.label + "\n" )
            else:
                spn_graph.node(transition.label, shape='rectangle', label='', width='0.2', height='0.6',
                               fixedsize='true', xlabel=transition.label + "\n")
        else:
            if rankdir == "TB":
                spn_graph.node(transition.label, shape='rectangle', style='filled', color='black', label='',
                               width='0.6', height='0.2', fixedsize='true',
                               xlabel=transition.label + "\n" )
            else:
                spn_graph.node(transition.label, shape='rectangle', style='filled', color='black', label='',
                               width='0.2', height='0.6', fixedsize='true',
                               xlabel=transition.label + "\n" )

        for input_arc in transition.input_arcs:
            label = str(input_arc.multiplicity) if input_arc.multiplicity > 1 else ""
            spn_graph.edge(input_arc.from_place.label, transition.label, label=label)

        for output_arc in transition.output_arcs:
            label = str(output_arc.multiplicity) if output_arc.multiplicity > 1 else ""
            spn_graph.edge(transition.label, output_arc.to_place.label, label=label)

        for inhibitor_arc in transition.inhibitor_arcs:
            label = str(inhibitor_arc.multiplicity) if inhibitor_arc.multiplicity > 1 else ""
            spn_graph.edge(inhibitor_arc.from_place.label, transition.label, arrowhead="dot", label=label)

    spn_graph.render(f'../output/graphs/{file}', view=show)
    return spn_graph
