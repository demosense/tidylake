"""Mermaid diagram generation and rendering."""

import re

from src.tidylake.core.context import TidyLakeContext


def visualize(context: TidyLakeContext, mermaid: bool = False, textual: bool = False) -> None:
    """Visualize the process in different formats.

    Args:
        context: Context instance to visualize.
        mermaid: If True, generate a Mermaid diagram.
        textual: If True, open a Textual TUI to inspect the graph.
    """
    if textual:
        from tidylake.visualization.textual_viewer import run_textual_viewer

        run_textual_viewer(context)
        return

    if mermaid:
        _render_mermaid(context)
    else:
        _render_list(context)


def _build_mermaid_lines(
    context: TidyLakeContext,
    *,
    include_labels: bool = True,
    include_classdefs: bool = True,
    use_dotted: bool = False,
) -> list[str]:
    """Build Mermaid diagram lines structure.

    Args:
        context: Context instance.
        include_labels: Include node labels.
        include_classdefs: Include class definitions for styling.
        use_dotted: Use dotted arrows for external dependencies.

    Returns:
        List of Mermaid diagram lines.
    """

    def sanitize(name: str) -> str:
        return re.sub(r"[^0-9A-Za-z_]", "_", name)

    def node_label(name: str) -> str:
        return name.replace("_", " ").title() if include_labels else name

    lines: list[str] = ["flowchart TD"]

    defined_data_products = {name: sanitize(name) for name in context.get_graph_sequence()}
    external_nodes: dict[str, str] = {}

    if include_labels:
        for original_name, node_id in defined_data_products.items():
            lines.append(f'    {node_id}["{node_label(original_name)}"]')

    for name in context.get_graph_sequence():
        data_product = context.data_products[name]
        for input_name in data_product.inputs:
            if input_name in defined_data_products:
                lines.append(f"    {defined_data_products[input_name]} --> {defined_data_products[name]}")
            else:
                ext_id = f"ext_{sanitize(input_name)}"
                if ext_id not in external_nodes:
                    external_nodes[ext_id] = node_label(input_name)
                    if include_labels:
                        lines.append(f'    {ext_id}["{node_label(input_name)}"]')
                arrow = "-.->" if use_dotted else "-->"
                lines.append(f"    {ext_id} {arrow} {defined_data_products[name]}")

    if include_labels and external_nodes and include_classdefs:
        lines.append("    classDef external fill:#f5f5f5,stroke:#999,stroke-width:1px;")
        for ext_id in external_nodes:
            lines.append(f"    {ext_id}:::external")

    return lines


def _render_mermaid(context: TidyLakeContext) -> None:
    """Render Mermaid diagram to stdout."""
    lines = _build_mermaid_lines(context, include_labels=True, include_classdefs=True)
    print("```mermaid")
    for line in lines:
        print(line)
    print("```")


def _render_list(context: TidyLakeContext) -> None:
    """Render simple numbered list of data_products."""
    for i, name in enumerate(context.get_graph_sequence(), 1):
        print(f"{i:02d}. {name}")
