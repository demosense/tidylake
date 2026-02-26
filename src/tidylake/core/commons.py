import os

DEFAULT_CONFIG_FILE = "./tidylake.yml"
TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE_DEFAULT = 10

EXECUTION_MODE_INTERACTIVE = "interactive"
EXECUTION_MODE_SCRIPT = "script"


def get_execution_mode() -> str:
    """
    Checks if the execution is an interactive jupyter session or a script.

    Returns:
        str: "interactive" if running in a Jupyter notebook, "script" otherwise.
    """

    try:
        # Check if the 'get_ipython' function is available,
        # which indicates a Jupyter environment
        get_ipython()  # type: ignore
        return EXECUTION_MODE_INTERACTIVE
    except NameError:
        # If 'get_ipython' is not defined, we are likely running in a script
        return EXECUTION_MODE_SCRIPT


execution_mode = get_execution_mode()


def get_use_synthetic_data() -> bool:
    """
    Checks if the environment variable 'TIDYLAKE_USE_SYNTHETIC_DATA' is set to 'true'.

    Returns:
        bool: True if 'TIDYLAKE_USE_SYNTHETIC_DATA' is set to 'true', False otherwise.
    """
    return os.getenv("TIDYLAKE_USE_SYNTHETIC_DATA", "false").lower() == "true"


def get_use_synthetic_data_sample_size() -> int:
    """
    Checks if the environment variable 'TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE' is set.

    Returns:
        int: The sample size for synthetic data generation, or default if not set.
    """
    return int(
        os.getenv(
            "TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE",
            TIDYLAKE_USE_SYNTHETIC_DATA_SAMPLE_SIZE_DEFAULT,
        )
    )
