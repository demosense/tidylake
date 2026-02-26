import ast


def get_decorator_name(decorator):
    """
    Return the fully qualified decorator name from an AST node.

    This walks through possible decorator node shapes to reconstruct a dotted
    name such as "data_product.add_raw_input". Decorators can appear as:
    - ast.Name: a simple name like "decorator"
    - ast.Attribute: an attribute access like "data_product.add_input"
    - ast.Call: a decorator with arguments like "@decorator(arg)"; in that case
      we recursively take its .func to get the name and ignore arguments here.
    """
    if isinstance(decorator, ast.Name):
        return decorator.id
    elif isinstance(decorator, ast.Attribute):
        value = get_decorator_name(decorator.value)
        return f"{value}.{decorator.attr}"
    elif isinstance(decorator, ast.Call):
        return get_decorator_name(decorator.func)
    return "<unknown>"


def parse_script_inputs(source_code: str) -> list[str]:
    """
    Parse a Python source string and extract input names referenced in the code.

    The function looks for two patterns using the Python AST:

    1) Assignment calls that read inputs via something like:
       "var = data_product.read_input("some_input")". In this case we collect the
       literal string argument to `read_input`.

    2) Function definitions decorated with `@data_product.add_input` (non-raw). We add
       the function name as an input name (with caveats noted inline).

    Using the AST (rather than string parsing) makes this resilient to
    whitespace, comments, and formatting differences while remaining explicit
    about the shapes of nodes we accept.
    """

    tree = ast.parse(source_code)
    results = []

    # Walk the entire AST tree; this yields every node regardless of depth.
    for node in ast.walk(tree):
        # Parse assignment calls
        if isinstance(node, ast.Assign):
            # Handle simple assignment expressions of the form:
            #   target = data_product.read_input("name")
            # We only care about the right-hand side (node.value).
            v = node.value
            if isinstance(v, ast.Call):
                # The callee can be many shapes. For `data_product.read_input("...")`,
                # v.func is an ast.Attribute whose .attr is "read_input" and
                # whose .value is typically an ast.Name("data_product"). We only need
                # the attribute name to recognize the call.
                func_name = v.func.attr if isinstance(v.func, ast.Attribute) else None

                # Ensure the call is exactly to something ending with
                # ".read_input" and that the first positional arg is a string
                # literal. We ignore non-literal or computed arguments.
                if func_name == "read_input" and v.args and isinstance(v.args[0], ast.Constant):
                    # The input name is the value of the string literal.
                    results.append(v.args[0].value)

        # Parse function def with add_input decorators
        if isinstance(node, ast.FunctionDef):
            # For functions, collect decorators and look for `@data_product.add_input`.
            function_name = node.name
            # Convert decorator AST nodes into dotted names for easy matching.
            decorators = [get_decorator_name(d) for d in node.decorator_list]
            for d in decorators:
                # NOTE: This is a heuristic. We only match the decorator name
                #       and exclude functions containing "raw" in their name.
                #       A more robust approach would inspect decorator args.
                # TODO: raw should be checked from argument not function name
                if d == "data_product.add_input" and "raw" not in function_name:
                    # TODO: name can be overwritten by decorator argument
                    # Here we use the function name as the input identifier.
                    results.append(function_name)

    return results
