from tidylake.plugins.compute_engine import ComputeEnginePlugin


class DummyComputeEnginePlugin(ComputeEnginePlugin):
    def read_dataset(self, name: str):
        raise NotImplementedError

    def read_synthetic_dataset(self, manifest_schema: dict):
        raise NotImplementedError

    def write_dataset(self, name: str, df):
        raise NotImplementedError

    def check_catalog_exists(self, name: str):
        raise NotImplementedError

    def get_schema_from_catalog(self, name: str):
        raise NotImplementedError

    def manifest_schema_to_engine_schema(self, manifest_schema: str):
        raise NotImplementedError

    def engine_schema_to_manifest_schema(self, catalog_schema):
        raise NotImplementedError

    def create_table(self, name: str, manifest_schema: str):
        raise NotImplementedError

    def validate_dataset_schema(self, manifest_schema, df):
        return NotImplementedError

    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        raise NotImplementedError

    def alter_table_drop_column(self, table_name: str, column_name: str):
        raise NotImplementedError

    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        raise NotImplementedError


def test_compute_changeset_detects_add_drop_alter():
    manifest = {
        "properties": {
            "id": {"type": "string"},
            "new_col": {"type": "integer"},
        }
    }

    catalog = {
        "properties": {
            "id": {"type": "number"},  # will trigger ALTER
            "legacy": {"type": "boolean"},  # will trigger DROP
        }
    }

    changeset = ComputeEnginePlugin.compute_changeset(manifest, catalog)

    assert ("ADD", "new_col", "integer") in changeset
    assert ("DROP", "legacy", None) in changeset
    assert ("ALTER", "id", "string") in changeset


def test_compute_changeset_handles_empty_catalog():
    manifest = {"properties": {"id": {"type": "string"}}}
    changeset = ComputeEnginePlugin.compute_changeset(manifest, {})
    assert changeset == [("ADD", "id", "string")]


def test_generate_synthetic_data_uses_manifest_types():
    manifest = {
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "score": {"type": "number"},
            "active": {"type": "boolean"},
            "misc": {"type": "object"},
        }
    }

    plugin = DummyComputeEnginePlugin()
    data = plugin.generate_synthetic_data_from_manifest(manifest)

    # Default sample size is defined in commons; assume >= 1
    sample_size = len(next(iter(data.values())))
    assert sample_size > 0

    assert all(val == "sample_name" for val in data["name"])
    assert all(isinstance(val, int) for val in data["age"])
    assert all(isinstance(val, float) for val in data["score"])
    assert all(isinstance(val, bool) for val in data["active"])
    assert all(val is None for val in data["misc"])


class RecordingComputeEngine(DummyComputeEnginePlugin):
    def __init__(self, exists: bool, catalog_schema=None):
        super().__init__()
        self._exists = exists
        self._catalog_schema = catalog_schema or {"properties": {"id": {"type": "string"}}}
        self.operations = []

    def check_catalog_exists(self, name: str):
        return self._exists

    def get_schema_from_catalog(self, name: str):
        return self._catalog_schema

    def create_table(self, name: str, manifest_schema: str):
        self.operations.append(("create", name, manifest_schema))

    def alter_table_add_column(self, table_name: str, column_name: str, column_type: str):
        self.operations.append(("add", table_name, column_name, column_type))

    def alter_table_drop_column(self, table_name: str, column_name: str):
        self.operations.append(("drop", table_name, column_name))

    def alter_table_alter_column(self, table_name: str, column_name: str, column_type: str):
        self.operations.append(("alter", table_name, column_name, column_type))


def test_update_or_create_schema_creates_when_missing():
    manifest = {"properties": {"id": {"type": "string"}}}
    engine = RecordingComputeEngine(exists=False)

    engine.update_or_create_schema("bronze", manifest, commit=True)

    assert ("create", "bronze", manifest) in engine.operations


def test_update_or_create_schema_dry_run_skips_creation():
    manifest = {"properties": {"id": {"type": "string"}}}
    engine = RecordingComputeEngine(exists=False)

    engine.update_or_create_schema("bronze", manifest, commit=False)

    assert engine.operations == []


def test_update_or_create_schema_applies_changes():
    manifest = {
        "properties": {
            "id": {"type": "string"},
            "new_col": {"type": "integer"},
        }
    }
    catalog = {
        "properties": {
            "id": {"type": "number"},
            "legacy": {"type": "boolean"},
        }
    }

    engine = RecordingComputeEngine(exists=True, catalog_schema=catalog)

    engine.update_or_create_schema("bronze", manifest, commit=True)

    assert ("add", "bronze", "new_col", "integer") in engine.operations
    assert ("drop", "bronze", "legacy") in engine.operations
    assert ("alter", "bronze", "id", "string") in engine.operations
