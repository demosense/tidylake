from unittest.mock import Mock, patch

import pytest

from tidylake.core.context import TidyLakeContext
from tidylake.core.data_product import DataProduct


def test_context_initialization():
    """Test context instance creation."""
    context = TidyLakeContext(name="test_context")

    assert context.name == "test_context"
    assert len(context.data_products) == 0


def test_add_data_product():
    """Test adding data_products."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []

    context.add_data_product(data_product)

    assert "test_data_product" in context.data_products
    assert context.data_products["test_data_product"] == data_product


def test_get_data_product_existing():
    """Test getting existing data_product."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    context.add_data_product(data_product)

    result = context.get_data_product("test_data_product")
    assert result == data_product


def test_get_data_product_missing():
    """Test getting non-existent data_product raises error."""
    context = TidyLakeContext(name="test_context")

    with pytest.raises(ValueError, match="'missing' not found"):
        context.get_data_product("missing")


def test_get_dependencies():
    """Test getting dependency map."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = ["input1"]
    context.add_data_product(data_product)

    deps = context.get_dependencies()
    assert deps == {"test_data_product": ("input1",)}


def test_get_graph_sequence_simple():
    """Test topological ordering of data_products."""
    context = TidyLakeContext(name="test_context")

    data_product1 = Mock(spec=DataProduct)
    data_product1.name = "data_product1"
    data_product1.inputs = []

    data_product2 = Mock(spec=DataProduct)
    data_product2.name = "data_product2"
    data_product2.inputs = ["data_product1"]

    context.add_data_product(data_product1)
    context.add_data_product(data_product2)

    sequence = context.get_graph_sequence()

    assert sequence == ["data_product1", "data_product2"]


def test_get_graph_sequence_cycle_detection(capsys):
    """Test cycle detection in dependencies."""
    context = TidyLakeContext(name="test_context")

    data_product1 = Mock(spec=DataProduct)
    data_product1.name = "data_product1"
    data_product1.inputs = ["data_product2"]

    data_product2 = Mock(spec=DataProduct)
    data_product2.name = "data_product2"
    data_product2.inputs = ["data_product1"]

    context.add_data_product(data_product1)
    context.add_data_product(data_product2)

    result = context.get_graph_sequence()
    captured = capsys.readouterr()

    assert result is None
    assert "Cycle detected" in captured.out


def test_run_data_product():
    """Test running individual data_product."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []

    context.add_data_product(data_product)
    context.run_data_product("test_data_product")

    data_product.run.assert_called_once()


def test_run_data_product_missing(capsys):
    """Test running non-existent data_product."""
    context = TidyLakeContext(name="test_context")

    context.run_data_product("missing")
    captured = capsys.readouterr()

    assert "not defined" in captured.out


def test_run_single_data_product():
    """Test running single data_product."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    context.add_data_product(data_product)

    with patch.object(context, "get_graph_sequence", return_value=["test_data_product"]):
        context.run("test_data_product", continue_run=False)

    data_product.run.assert_called_once()


def test_run_continue_from_data_product():
    """Test running from specific data_product onwards."""
    context = TidyLakeContext(name="test_context")
    data_product1 = Mock(spec=DataProduct)
    data_product1.name = "data_product1"
    data_product1.inputs = []
    data_product2 = Mock(spec=DataProduct)
    data_product2.name = "data_product2"
    data_product2.inputs = []
    context.add_data_product(data_product1)
    context.add_data_product(data_product2)

    with patch.object(context, "get_graph_sequence", return_value=["data_product1", "data_product2"]):
        context.run("data_product2", continue_run=True)

    data_product1.run.assert_not_called()
    data_product2.run.assert_called_once()


def test_peek_data_product():
    """Test peeking into data_product."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    context.add_data_product(data_product)

    context.peek_data_product("test_data_product")

    data_product.peek.assert_called_once()


def test_peek_data_product_missing(capsys):
    """Test peeking non-existent data_product."""
    context = TidyLakeContext(name="test_context")

    context.peek_data_product("missing")
    captured = capsys.readouterr()

    assert "not defined" in captured.out


def test_schema_diff_no_compute_engine(capsys):
    """Test schema diff without compute engine."""
    context = TidyLakeContext(name="test_context")

    context.schema_diff()
    captured = capsys.readouterr()

    assert "No compute engine" in captured.out


def test_schema_update_no_compute_engine(capsys):
    """Test schema update without compute engine."""
    context = TidyLakeContext(name="test_context")

    context.schema_update()
    captured = capsys.readouterr()

    assert "No compute engine" in captured.out


def test_visualize_default(capsys):
    """Test default visualization."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    context.add_data_product(data_product)

    with patch.object(context, "get_graph_sequence", return_value=["test_data_product"]):
        context.visualize()

    captured = capsys.readouterr()
    assert "01. test_data_product" in captured.out


def test_visualize_mermaid(capsys):
    """Test Mermaid visualization."""
    context = TidyLakeContext(name="test_context")
    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    context.add_data_product(data_product)

    with patch.object(context, "get_graph_sequence", return_value=["test_data_product"]):
        context.visualize(mermaid=True)

    captured = capsys.readouterr()
    assert "```mermaid" in captured.out
    assert "flowchart TD" in captured.out


def test_visualize_textual():
    """Test textual visualization."""
    context = TidyLakeContext(name="test_context")

    with patch("tidylake.visualization.textual_viewer.run_textual_viewer") as mock_textual:
        context.visualize(textual=True)

    mock_textual.assert_called_once_with(context)


def test_schema_diff_with_compute_engine():
    """Test schema diff with compute engine."""
    context = TidyLakeContext(name="test_context")
    mock_engine = Mock()
    context.compute_engine = mock_engine

    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    data_product.compute_engine = mock_engine
    data_product.get_schemas.return_value = {"test": "schema"}
    context.add_data_product(data_product)

    result = context.schema_diff("test_data_product")

    assert result == {"test_data_product": {"test": "schema"}}


def test_schema_update_with_compute_engine():
    """Test schema update with compute engine."""
    context = TidyLakeContext(name="test_context")
    mock_engine = Mock()
    context.compute_engine = mock_engine

    data_product = Mock(spec=DataProduct)
    data_product.name = "test_data_product"
    data_product.inputs = []
    data_product.compute_engine = mock_engine
    data_product.schema = {"type": "object"}
    context.add_data_product(data_product)

    context.schema_update("test_data_product", commit=True)

    data_product.update_or_create_schema.assert_called_once_with(commit=True)


def test_run_no_data_products_in_sequence():
    """Test run with empty data_product sequence."""
    context = TidyLakeContext(name="test_context")

    with patch.object(context, "get_graph_sequence", return_value=[]):
        context.run(None, continue_run=False)

    # Should complete without error


def test_run_data_product_not_in_sequence():
    """Test run with data_product not in sequence."""
    context = TidyLakeContext(name="test_context")

    with patch.object(context, "get_graph_sequence", return_value=["other_data_product"]):
        context.run("missing_data_product", continue_run=False)

    # Should run from index 0 when data_product not found
