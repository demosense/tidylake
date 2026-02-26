from unittest.mock import Mock

from tidylake.visualization.textual_viewer import GraphApp


def test_compose_layout():
    """Test compose method creates proper layout."""
    context = Mock()
    context.name = "Test"
    context.get_dependencies.return_value = {}
    context.get_graph_sequence.return_value = []
    context.data_products = {}

    app = GraphApp(context)

    # Test that compose doesn't raise errors
    result = app.compose()
    assert result is not None


def test_add_structure_with_dict():
    """Test _add_structure with dictionary values."""
    context = Mock()
    context.name = "Test"
    context.get_dependencies.return_value = {}
    context.get_graph_sequence.return_value = []
    context.data_products = {}

    app = GraphApp(context)

    from textual.widgets import Tree

    tree = Tree("root")
    parent = tree.root.add("parent")

    app._add_structure(parent, "config", {"nested": {"key": "value"}})

    assert len(parent.children) > 0


def test_add_structure_with_list():
    """Test _add_structure with list values."""
    context = Mock()
    context.name = "Test"
    context.get_dependencies.return_value = {}
    context.get_graph_sequence.return_value = []
    context.data_products = {}

    app = GraphApp(context)

    from textual.widgets import Tree

    tree = Tree("root")
    parent = tree.root.add("parent")

    app._add_structure(parent, "items", ["item1", "item2"])

    assert len(parent.children) > 0


def test_add_structure_with_primitive():
    """Test _add_structure with primitive values."""
    context = Mock()
    context.name = "Test"
    context.get_dependencies.return_value = {}
    context.get_graph_sequence.return_value = []
    context.data_products = {}

    app = GraphApp(context)

    from textual.widgets import Tree

    tree = Tree("root")
    parent = tree.root.add("parent")

    app._add_structure(parent, "value", "simple_string")

    assert len(parent.children) > 0
