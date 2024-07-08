from .spn import *
from graphviz import Digraph


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

    # Add a text box at the top left of the diagram for the dimension summary with a gray background
    spn_graph.attr('node', shape='plaintext', style='filled', fillcolor='lightgrey')
    spn_graph.node('dimension_summary', label=dimension_summary)
    spn_graph.attr('node', shape='ellipse', style='', fillcolor='')

    # Draw places and marking
    for place in spn.places:
        token_count = len(place.tokens)  # Get the count of tokens from the tokens list

        if place.is_dimension_holder:
            # Dimension holders are displayed differently
            label = f"{place.label}\n{place.dimension_tracked} = {place.value:.2f}"
            spn_graph.node(place.label, label=label, shape="ellipse", style='filled', fillcolor="lightblue", fontsize='10')
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
            # Adjust transition node and label based on the rankdir and type
            if rankdir == "TB":
                spn_graph.node(transition.label, shape='rectangle', label='', width='0.6', height='0.2',
                               fixedsize='true', xlabel=transition.label + "\n" + (
                        str(list(transition.distribution.keys())[0]) if transition.distribution else "T"))
            else:
                spn_graph.node(transition.label, shape='rectangle', label='', width='0.2', height='0.6',
                               fixedsize='true', xlabel=transition.label + "\n" + (
                        str(list(transition.distribution.keys())[0]) if transition.distribution else "T"))
        else:
            if rankdir == "TB":
                spn_graph.node(transition.label, shape='rectangle', style='filled', color='black', label='',
                               width='0.6', height='0.2', fixedsize='true',
                               xlabel=transition.label + "\n" + str(transition.weight))
            else:
                spn_graph.node(transition.label, shape='rectangle', style='filled', color='black', label='',
                               width='0.2', height='0.6', fixedsize='true',
                               xlabel=transition.label + "\n" + str(transition.weight))

        # Draw arcs
        for input_arc in transition.input_arcs:
            label = str(input_arc.multiplicity) if input_arc.multiplicity > 1 else ""
            spn_graph.edge(input_arc.from_place.label, transition.label, label=label)

        for output_arc in transition.output_arcs:
            label = str(output_arc.multiplicity) if output_arc.multiplicity > 1 else ""
            spn_graph.edge(transition.label, output_arc.to_place.label, label=label)

        for inhibitor_arc in transition.inhibitor_arcs:
            label = str(inhibitor_arc.multiplicity) if inhibitor_arc.multiplicity > 1 else ""
            spn_graph.edge(inhibitor_arc.from_place.label, transition.label, arrowhead="dot", label=label)

    spn_graph.render(f'output/graphs/{file}', view=show)
    return spn_graph
