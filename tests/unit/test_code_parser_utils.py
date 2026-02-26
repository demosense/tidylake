import textwrap

from tidylake.utils.code_parser import parse_script_inputs


def test_parse_script_inputs_from_read_input():
    source = textwrap.dedent(
        """
        df_bronze = data_product.read_input("bronze_customers")
        df_profile = other.read_input("bronze_profile")
        """
    )

    assert parse_script_inputs(source) == ["bronze_customers", "bronze_profile"]


def test_parse_script_inputs_from_decorator():
    source = textwrap.dedent(
        """
        @data_product.add_input()
        def bronze_customers():
            ...

        @data_product.add_input(raw=True)
        def raw_customers():
            ...
        """
    )

    assert parse_script_inputs(source) == ["bronze_customers"]


def test_parse_script_inputs_ignores_dynamic_calls():
    source = textwrap.dedent(
        """
        name = "dynamic"
        df = data_product.read_input(name)
        """
    )

    assert parse_script_inputs(source) == []
