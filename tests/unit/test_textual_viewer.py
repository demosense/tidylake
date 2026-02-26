from textual.widgets import Tree

from tidylake.visualization.textual_viewer import GraphApp


class DummyDataProduct:
    def __init__(self):
        self.inputs = ["bronze", "external"]
        self.schema = {
            "properties": {
                "col": {"type": "string", "description": "Sample"},
                "nums": [1, {"nested": "value"}],
            }
        }


class DummyPipeline:
    name = "Acceptance"

    def __init__(self):
        self.data_products = {"bronze": DummyDataProduct(), "silver": DummyDataProduct()}

    def get_graph_sequence(self):
        return ["bronze", "silver"]

    def get_dependencies(self):
        return {"silver": ("bronze", "external"), "bronze": tuple()}


def test_textual_viewer_populate_tree_sections():
    context = DummyPipeline()
    app = GraphApp(context)
    tree = Tree("root")

    app._populate_tree(tree)

    assert len(tree.root.children) == 2

    bronze_node = tree.root.children[0]
    bronze_labels = [child.label.plain for child in bronze_node.children]
    assert any("Downstream" in lbl for lbl in bronze_labels)

    silver_node = tree.root.children[1]
    labels = [child.label.plain for child in silver_node.children]
    assert any("Inputs" in lbl for lbl in labels)
    assert any("Schema" in lbl for lbl in labels)


def test_textual_viewer_add_structure_handles_list():
    context = DummyPipeline()
    app = GraphApp(context)
    tree = Tree("root")

    schema_node = tree.root.add("Schema")
    app._add_structure(schema_node, "nums", [1, 2, {"nested": "value"}])

    assert schema_node.children
    list_node = schema_node.children[0]
    assert "list" in list_node.label.plain
    assert list_node.children


def test_textual_viewer_dependents_mapping():
    context = DummyPipeline()
    app = GraphApp(context)

    deps = app._build_dependents()
    assert deps["bronze"] == ["silver"]
    assert deps["silver"] == []
