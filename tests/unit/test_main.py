from unittest.mock import Mock, patch

from typer.testing import CliRunner

from tidylake.cli.commands import app


def test_list_command_default():
    """Test list command with default options."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        mock_context.visualize.assert_called_once_with(mermaid=False, textual=False)


def test_list_command_mermaid():
    """Test list command with mermaid flag."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["list", "--mermaid"])

        assert result.exit_code == 0
        mock_context.visualize.assert_called_once_with(mermaid=True, textual=False)


def test_list_command_textual():
    """Test list command with textual flag."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["list", "--textual"])

        assert result.exit_code == 0
        mock_context.visualize.assert_called_once_with(mermaid=False, textual=True)


def test_list_command_mutually_exclusive_flags():
    """Test list command with mutually exclusive flags fails."""
    runner = CliRunner()
    result = runner.invoke(app, ["list", "--mermaid", "--textual"])

    assert result.exit_code != 0
    assert "Mermaid and Textual modes are mutually" in result.output


def test_run_command_default():
    """Test run command with default options."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["run"])

        assert result.exit_code == 0
        mock_context.run.assert_called_once_with(name=None, continue_run=False)


def test_run_command_with_data_product():
    """Test run command with specific data_product."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["run", "--data-product", "test_data_product"])

        assert result.exit_code == 0
        mock_context.run.assert_called_once_with(name="test_data_product", continue_run=False)


def test_run_command_continue():
    """Test run command with continue flag."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["run", "--continue-run"])

        assert result.exit_code == 0
        mock_context.run.assert_called_once_with(name=None, continue_run=True)


def test_peek_command():
    """Test peek command."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["peek", "--data-product", "test_data_product"])

        assert result.exit_code == 0
        mock_context.peek_data_product.assert_called_once_with(name="test_data_product")


def test_schema_diff_command():
    """Test schema diff command."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_context.schema_diff.return_value = {}
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["schema", "diff"])

        assert result.exit_code == 0
        mock_context.schema_diff.assert_called_once_with(name=None)


def test_schema_diff_command_renders_table():
    """Test schema diff command renders table output."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_context.schema_diff.return_value = {
            "test_data_product": {
                "defined_schema": {"properties": {"id": {"type": "string"}}},
                "catalog_schema": {"properties": {"id": {"type": "integer"}}},
            }
        }
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["schema", "diff"])

        assert result.exit_code == 0
        assert "test_data_product" in result.output


def test_schema_update_command():
    """Test schema update command."""
    with patch("tidylake.cli.commands.create_context_from_config") as mock_create:
        mock_context = Mock()
        mock_create.return_value = mock_context

        runner = CliRunner()
        result = runner.invoke(app, ["schema", "update", "--commit"])

        assert result.exit_code == 0
        mock_context.schema_update.assert_called_once_with(name=None, commit=True)
