def serialize_datetimes(obj):
    """
    Recursively convert all datetime objects in a nested structure (dict, list, etc.) to ISO format strings.

    Args:
        obj: The object to process (can be dict, list, datetime, or other)

    Returns:
        The object with all datetime objects converted to ISO strings.
    """
    import datetime
    if isinstance(obj, dict):
        return {k: serialize_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetimes(v) for v in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return obj 