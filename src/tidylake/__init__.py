"""tidylake Framework."""

# Backward compatibility - expose main classes at package level
from .core import DataProduct, TidyLakeContext, get_or_create_context
from .scaffold import create_project_structure

__all__ = ["TidyLakeContext", "DataProduct", "get_or_create_context", "create_project_structure"]
