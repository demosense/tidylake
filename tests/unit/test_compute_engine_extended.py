from unittest.mock import Mock, patch

from tidylake.plugins.compute_engine import ComputeEnginePlugin


def test_update_or_create_schema_no_changes(capsys):
    """Test schema update with no changes needed."""
    plugin = Mock(spec=ComputeEnginePlugin)
    plugin.check_catalog_exists.return_value = True
    plugin.get_schema_from_catalog.return_value = {"properties": {"id": {"type": "string"}}}
    plugin.compute_changeset.return_value = []  # No changes

    # Call the actual method
    ComputeEnginePlugin.update_or_create_schema(
        plugin, "test_table", {"properties": {"id": {"type": "string"}}}, commit=True
    )

    captured = capsys.readouterr()
    assert "Schema changes for table test_table:" in captured.out


def test_update_or_create_schema_table_missing_dry_run(capsys):
    """Test schema update for missing table in dry run mode."""
    plugin = Mock(spec=ComputeEnginePlugin)
    plugin.check_catalog_exists.return_value = False

    ComputeEnginePlugin.update_or_create_schema(
        plugin, "test_table", {"properties": {"id": {"type": "string"}}}, commit=False
    )

    captured = capsys.readouterr()
    assert "A new table will be created" in captured.out
    assert "Dry run mode" in captured.out


def test_generate_synthetic_data_edge_cases():
    """Test synthetic data generation with edge cases."""
    plugin = Mock(spec=ComputeEnginePlugin)

    manifest = {
        "properties": {
            "unknown_type": {"type": "unknown"},
            "null_type": {"type": None},
        }
    }

    with patch(
        "tidylake.plugins.compute_engine.get_use_synthetic_data_sample_size",
        return_value=2,
    ):
        data = ComputeEnginePlugin.generate_synthetic_data_from_manifest(plugin, manifest)

    assert len(data["unknown_type"]) == 2
    assert all(val is None for val in data["unknown_type"])
    assert all(val is None for val in data["null_type"])


def test_compute_changeset_empty_manifest():
    """Test changeset computation with empty manifest."""
    manifest = {"properties": {}}
    catalog = {"properties": {"old_col": {"type": "string"}}}

    changeset = ComputeEnginePlugin.compute_changeset(manifest, catalog)

    assert changeset == [("DROP", "old_col", None)]


def test_compute_changeset_no_properties():
    """Test changeset computation with no properties key."""
    manifest = {}
    catalog = {}

    changeset = ComputeEnginePlugin.compute_changeset(manifest, catalog)

    assert changeset == []
