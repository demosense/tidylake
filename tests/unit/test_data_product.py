from unittest.mock import Mock, mock_open, patch

import pytest

from tidylake.core.data_product import DataProduct


def test_data_product_initialization():
    """Test data_product instance creation."""
    data_product = DataProduct(name="test_data_product", schema={"type": "object"}, script="print('test')")

    assert data_product.name == "test_data_product"
    assert data_product.schema == {"type": "object"}
    assert data_product.script == "print('test')"


def test_data_product_inputs_extraction():
    """Test extracting inputs from data_product configuration."""
    data_product = DataProduct(
        name="test_data_product", schema={"type": "object"}, script="# inputs: input1, input2"
    )

    assert hasattr(data_product, "inputs")


@patch("tidylake.core.data_product.Path.is_file")
@patch("builtins.open", new_callable=mock_open, read_data="data_product:\n  name: test")
def test_get_config_success(mock_file, mock_is_file):
    """Test successful config loading."""
    mock_is_file.return_value = True

    with patch("yaml.safe_load", return_value={"data_product": {"name": "test"}}):
        config = DataProduct.get_config("test.yml")

    assert config == {"data_product": {"name": "test"}}


@patch("tidylake.core.data_product.Path.is_file")
def test_get_config_file_not_found(mock_is_file):
    """Test config loading with missing file."""
    mock_is_file.return_value = False

    with pytest.raises(FileNotFoundError):
        DataProduct.get_config("missing.yml")


def test_set_compute_engine():
    """Test setting compute engine."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")
    engine = Mock()

    data_product.set_compute_engine(engine)

    assert data_product.compute_engine == engine


def test_read_input_no_compute_engine():
    """Test read_input without compute engine raises error."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    with pytest.raises(ValueError, match="Compute engine not set"):
        data_product.read_input("test")


def test_read_input_with_compute_engine():
    """Test read_input with compute engine."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")
    engine = Mock()
    engine.read_dataset.return_value = "data"
    data_product.set_compute_engine(engine)

    with patch("tidylake.core.data_product.get_use_synthetic_data", return_value=False):
        result = data_product.read_input("test")

    assert result == "data"
    engine.read_dataset.assert_called_once_with("test")


def test_read_input_uses_synthetic_dataset():
    """Test read_input uses synthetic data when enabled."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")
    engine = Mock()
    engine.read_synthetic_dataset.return_value = "synthetic_data"
    data_product.set_compute_engine(engine)

    with patch("tidylake.core.data_product.get_use_synthetic_data", return_value=True):
        result = data_product.read_input("test")

    assert result == "synthetic_data"
    engine.read_synthetic_dataset.assert_called_once_with({})


def test_peek_no_compute_engine():
    """Test peek without compute engine raises error."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    with pytest.raises(ValueError, match="Compute engine not set"):
        data_product.peek()


def test_peek_with_compute_engine():
    """Test peek with compute engine."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")
    engine = Mock()
    engine.read_dataset.return_value = "data"
    data_product.set_compute_engine(engine)

    with patch("tidylake.core.data_product.get_use_synthetic_data", return_value=False):
        data_product.peek()

    engine.display_dataset.assert_called_once_with("data")


def test_get_schemas_with_compute_engine():
    """Test get_schemas with compute engine."""
    data_product = DataProduct(name="test_data_product", schema={"type": "object"}, script="")

    engine = Mock()
    engine.get_schema_from_catalog.return_value = {"catalog": "schema"}
    data_product.set_compute_engine(engine)

    result = data_product.get_schemas()

    assert result["defined_schema"] == {"type": "object"}
    assert result["catalog_schema"] == {"catalog": "schema"}


def test_update_or_create_schema_no_engine():
    """Test schema update without compute engine raises error."""
    data_product = DataProduct(name="test_data_product", schema={"type": "object"}, script="")

    with pytest.raises(ValueError, match="Compute engine or schema not set"):
        data_product.update_or_create_schema(commit=True)


def test_update_or_create_schema_with_engine():
    """Test schema update with compute engine."""
    data_product = DataProduct(name="test_data_product", schema={"type": "object"}, script="")

    engine = Mock()
    data_product.set_compute_engine(engine)

    data_product.update_or_create_schema(commit=True)

    engine.update_or_create_schema.assert_called_once_with(
        "test_data_product", {"type": "object"}, commit=True
    )


def test_run_interactive_mode(capsys):
    """Test run in interactive mode does nothing."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    with patch("tidylake.core.data_product.execution_mode", "interactive"):
        data_product.run()

    captured = capsys.readouterr()
    assert "WARN: Calling run from data product modules has no effect" in captured.out


def test_run_with_compute_engine_writes_dataset():
    """Test run with compute engine writes dataset."""
    data_product = DataProduct(name="test_data_product", schema={}, script="package.module")
    engine = Mock()
    data_product.set_compute_engine(engine)
    data_product.set_output_data("test_data")

    with (
        patch("tidylake.core.data_product.execution_mode", "script"),
        patch("tidylake.core.data_product.importlib.import_module"),
    ):
        data_product.run()

    engine.write_dataset.assert_called_once_with("test_data_product", "test_data")


def test_run_with_compute_engine_missing_output():
    """Test run with compute engine but no output data raises error."""
    data_product = DataProduct(name="test_data_product", schema={}, script="package.module")
    engine = Mock()
    data_product.set_compute_engine(engine)

    with (
        patch("tidylake.core.data_product.execution_mode", "script"),
        patch("tidylake.core.data_product.importlib.import_module"),
        pytest.raises(ValueError, match="No output data set"),
    ):
        data_product.run()


def test_add_input_decorator_returns_function():
    """Test add_input decorator returns wrapped function."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    @data_product.add_input()
    def test_func():
        return "test_data"

    result = test_func()
    assert result == "test_data"


def test_set_sink_wrapper_warns(capsys):
    """Test set_sink wrapper warns when called."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    @data_product.set_sink()
    def test_sink():
        pass

    test_sink()
    captured = capsys.readouterr()
    assert "WARN: Calling sink from data product modules has no effect" in captured.out


def test_set_output_data_no_compute_engine():
    """Test set_output_data without compute engine raises error."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")

    with pytest.raises(ValueError, match="Compute engine not set"):
        data_product.set_output_data("test_data")


def test_set_output_data():
    """Test setting output data."""
    data_product = DataProduct(name="test_data_product", schema={}, script="")
    engine = Mock()
    engine.read_dataset.return_value = "data"
    data_product.set_compute_engine(engine)

    data_product.set_output_data("test_data")

    assert data_product.output_data == "test_data"
