from typing import Type

from pydantic import BaseModel


def coerce_to_schema(data: dict, schema: Type[BaseModel]) -> dict:
    """
    For each field in the schema:
      - If present in data, validate/coerce (truncate strings, recurse for lists/models)
      - If missing, use default or raise error
      - Ignore extra fields
    """
    result = {}
    for name, field in schema.model_fields.items():
        if name in data:
            value = data[name]
            # Truncate strings
            if isinstance(value, str) and getattr(field, "max_length", None):
                value = value[: field.max_length]
            # Recurse for lists of models
            elif (
                isinstance(value, list)
                and hasattr(field.annotation, "__origin__")
                and field.annotation.__origin__ is list
                and hasattr(field.annotation.__args__[0], "model_fields")
            ):
                item_schema = field.annotation.__args__[0]
                value = [coerce_to_schema(item, item_schema) for item in value]
            # Recurse for nested models
            elif isinstance(value, dict) and hasattr(field.annotation, "model_fields"):
                value = coerce_to_schema(value, field.annotation)
            result[name] = value
        elif field.default is not None:
            result[name] = field.default
        elif getattr(field, "default_factory", None) is not None:
            result[name] = field.default_factory()
        else:
            raise ValueError(f"Missing required field: {name}")
    return result
