from pathlib import Path
from unittest.mock import mock_open, patch

from tidylake.core.data_product import DataProduct


def test_data_product_finds_script_in_same_directory_as_config():
    """Test that data_product finds Python script relative to config file directory."""
    # Given
    config_dir = Path("/some/path/demo/pandas_local")
    script_content = """# test script
input1 = data_product.read_input('input1')

@data_product.add_input
def input2():
    return data
"""

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=script_content)) as mock_file,
        patch("pathlib.Path.is_file", return_value=True),
    ):
        # When
        data_product = DataProduct(
            name="test_data_product",
            schema={},
            script="bronze_customers",
            config_dir=config_dir,
        )

        # Then
        expected_script_path = config_dir / "bronze_customers.py"
        mock_file.assert_called_with(expected_script_path)
        assert "input1" in data_product.inputs
        assert "input2" in data_product.inputs


def test_data_product_handles_missing_script_gracefully():
    """Test that data_product handles missing script files without crashing."""
    # Given
    config_dir = Path("/some/path/demo/pandas_local")

    # When
    with patch("pathlib.Path.is_file", return_value=False):
        data_product = DataProduct(
            name="test_data_product", schema={}, script="missing_script", config_dir=config_dir
        )

    # Then
    assert data_product.inputs == []
