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

from graphviz import Digraph


def draw_spn(spn, file="spn_default", show=True, print_place_labels=False, rankdir="TB"):
    spn_graph = Digraph(engine="dot", graph_attr={'rankdir': rankdir})

    # Fetch simulation time directly from the SPN object
    simulation_time = spn.simulation_time

    # Display simulation time explicitly
    dimension_summary = f"Simulation Clock:\nTime: {simulation_time:.2f}\n"

    # Sum all tracked dimension values from places and transitions
    dimension_totals = {}

    dimension_totals = {}
    for transition in spn.transitions:
        for dimension, value in transition.dimension_table.items():
            if dimension:
                dimension_totals[dimension] = dimension_totals.get(dimension, 0) + value

    # Add dimensions to the summary
    for dim, total_value in dimension_totals.items():
        dimension_summary += f"{dim}: {total_value:.2f}\n"

    summary_text = dimension_summary

    # Add a text box at the top left of the diagram for the summary with a gray background
    spn_graph.attr('node', shape='plaintext', style='filled', fillcolor='lightgrey')
    spn_graph.node('summary', label=summary_text)
    spn_graph.attr('node', shape='ellipse', style='', fillcolor='')

    # Draw places and marking
    for place in spn.places:
        token_count = len(place.tokens)  # Get the count of tokens from the tokens list

        if place.is_tracking:
            formatted_value = f"{place.value:.2f}"  # Display the value with two decimal precision
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

    # Draw transitions with external labels and tables beside them
    for transition in spn.transitions:
        # Draw the transition node with its original style
        if transition.dimension_changes:
            total_dimensions = spn.dimensions  # All dimensions from the SPN
            connected_dimensions = [dim for dim, _, _ in transition.dimension_changes]

            # Determine colors for each dimension
            colors = []
            for idx, dim in enumerate(total_dimensions):
                if idx == 0:  # Time dimension
                    if transition.t_type == "T":  # Timed transition
                        colors.append("white")
                    else:  # Immediate transition
                        colors.append("black")
                else:  # Other dimensions
                    colors.append("white" if dim in connected_dimensions else "black")

            # Create the striped style for the transition
            color_string = ":".join(colors)

            # Draw the transition as a striped rectangle
            spn_graph.node(
                transition.label,
                shape="rect",
                style="striped",
                fillcolor=color_string,
                label="",  # Ensure no label inside the rectangle
                xlabel=transition.label,  # External label below the rectangle
                height='0.2',
                width='0.6',
                fixedsize='true'
            )
        else:
            total_dimensions = spn.dimensions

            # Set the default colors for each dimension based on transition type
            colors = ["white" if dim == "time" and transition.t_type == "T" else "black" for dim in total_dimensions]

            # Create the striped style for the transition
            color_string = ":".join(colors)

            # Draw the transition as a striped rectangle
            spn_graph.node(
                transition.label,
                shape="rect",
                style="striped",
                fillcolor=color_string,
                label="",  # Ensure no label inside the rectangle
                xlabel=transition.label,  # External label below the rectangle
                height='0.2',
                width='0.6',
                fixedsize='true'
            )

        # Create a separate node to display the dimension table above and to the right of the transition
        if transition.dimension_table:
            # Define the table label using HTML-like syntax, excluding headers
            table_label = f"""<<table border='1' cellborder='1' cellspacing='0'>"""
            for dimension, value in transition.dimension_table.items():
                if dimension is not None:  # Avoid adding None keys
                    table_label += f"<tr><td>{dimension}</td><td>{value:.2f}</td></tr>"
            table_label += "</table>>"

            # Define labels for the nodes
            table_node_label = f"{transition.label}_table"
            spacer_node_label = f"{transition.label}_spacer"

            # Create an invisible spacer node above the transition
            spn_graph.node(spacer_node_label, label="", width="0", height="0", style="invis")

            # Create the table node
            spn_graph.node(table_node_label, shape="plaintext", label=table_label)

            # Connect the spacer node to the transition with an invisible edge
            spn_graph.edge(spacer_node_label, transition.label, style="invis")

            # Connect the table node to the spacer node with an invisible edge
            spn_graph.edge(spacer_node_label, table_node_label, style="invis")

        # Draw input arcs
        for input_arc in transition.input_arcs:
            label = str(input_arc.multiplicity) if input_arc.multiplicity > 1 else ""
            spn_graph.edge(input_arc.from_place.label, transition.label, label=label)

        # Draw output arcs
        for output_arc in transition.output_arcs:
            spn_graph.edge(transition.label, output_arc.to_place.label,
                           label=str(output_arc.multiplicity) if output_arc.multiplicity > 1 else "")

        # Draw inhibitor arcs
        for inhibitor_arc in transition.inhibitor_arcs:
            spn_graph.edge(inhibitor_arc.from_place.label, transition.label,
                           arrowhead="dot", label=str(inhibitor_arc.multiplicity) if inhibitor_arc.multiplicity > 1 else "")

    # Render the SPN graph
    spn_graph.render(f'../output/graphs/{file}', view=show)
    return spn_graph

