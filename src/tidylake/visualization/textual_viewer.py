from __future__ import annotations

from rich.markup import escape
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header, Static, Tree

from src.tidylake.core.context import TidyLakeContext  # type: ignore


def _format_input_label(context: TidyLakeContext, input_name: str) -> str:
    if input_name in context.data_products:
        return f"[green]{input_name}[/green]"
    return f"[yellow]{input_name}[/yellow] [dim](external)[/dim]"


class GraphApp(App):
    """Textual application to display a dependency graph."""

    CSS = """
    Screen {
        align: center middle;
    }

    #layout {
        height: 95%;
        width: 95%;
        padding: 1;
    }

    Tree {
        height: 100%;
        width: 3fr;
        border: solid #666;
        padding: 1;
        overflow: auto;
    }

    #help {
        width: 1fr;
        padding: 1;
        border: solid #333;
        height: 100%;
        overflow: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, context: TidyLakeContext):
        super().__init__()
        self._context = context
        self._dependencies = context.get_dependencies()
        self._dependents = self._build_dependents()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        tree = Tree(Text.from_markup(f"[bold]{self._context.name}[/bold]"), id="tree")
        self._populate_tree(tree)
        tree.focus()

        info = Static(
            "[b]Legend[/b]\n"
            "[green]green[/green] → upstream data product within this project\n"
            "[yellow]yellow[/yellow] → external input not defined as a data product\n\n"
            "[cyan]cyan[/cyan] → downstream data product depending on current data product\n\n"
            "Shortcuts: [b]q[/b] quit · [b]r[/b] refresh",
            id="help",
        )

        layout = Horizontal(tree, info, id="layout")
        yield Container(layout)
        yield Footer()

    def _populate_tree(self, tree: Tree[str]) -> None:
        tree.root.expand()

        for data_product_name in self._context.get_graph_sequence():
            data_product = self._context.data_products[data_product_name]
            node = tree.root.add(Text.from_markup(f"[bold]{data_product_name}[/bold]"))

            if data_product.inputs:
                inputs_node = node.add(Text.from_markup("[italic]Inputs[/italic]"))
                for input_name in data_product.inputs:
                    label = _format_input_label(self._context, input_name)
                    inputs_node.add(Text.from_markup(label))

            if data_product.schema:
                schema_node = node.add(Text.from_markup("[italic]Schema[/italic]"))
                schema_node.expand()
                for key, value in data_product.schema.items():
                    self._add_structure(schema_node, key, value)

            downstream = self._dependents.get(data_product_name, [])
            if downstream:
                downstream_node = node.add(Text.from_markup("[italic]Downstream[/italic]"))
                for dep in downstream:
                    downstream_node.add(Text.from_markup(f"[cyan]{dep}[/cyan]"))

    def action_refresh(self) -> None:
        self.refresh(layout=True)

    def _add_structure(self, parent, label, value, depth: int = 0) -> None:
        """Recursively render schema metadata."""
        label_text = escape(str(label)) if label is not None else ""

        if isinstance(value, dict):
            node_label = (
                Text.from_markup(f"[bold]{label_text or 'object'}[/bold] [dim](dict)[/dim]")
                if label_text
                else Text.from_markup("[bold]object[/bold] [dim](dict)[/dim]")
            )
            node = parent.add(node_label)
            if depth == 0:
                node.expand()
            if not value:
                node.add(Text.from_markup("[dim]<empty>[/dim]"))
            for sub_key, sub_value in value.items():
                self._add_structure(node, sub_key, sub_value, depth + 1)

        elif isinstance(value, list):
            node_label = (
                Text.from_markup(f"[bold]{label_text or 'list'}[/bold] [dim](list)[/dim]")
                if label_text
                else Text.from_markup("[bold]list[/bold] [dim](list)[/dim]")
            )
            node = parent.add(node_label)
            if depth == 0:
                node.expand()
            if not value:
                node.add(Text.from_markup("[dim]<empty>[/dim]"))
            for idx, item in enumerate(value):
                self._add_structure(node, f"[{idx}]", item, depth + 1)

        else:
            value_text = escape(str(value))
            if label_text:
                parent.add(Text.from_markup(f"[bold]{label_text}[/bold]: {value_text}"))
            else:
                parent.add(Text(value_text))

    def _build_dependents(self) -> dict[str, list[str]]:
        dependents: dict[str, list[str]] = {data_product: [] for data_product in self._context.data_products}
        for data_product_name, inputs in self._dependencies.items():
            for input_name in inputs:
                if input_name in dependents:
                    dependents[input_name].append(data_product_name)
        return dependents


def run_textual_viewer(context: TidyLakeContext) -> None:
    """Launch the Textual TUI to visualize the graph."""
    app = GraphApp(context)
    app.run()
