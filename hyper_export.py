import os
from decimal import Decimal
from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode, TableDefinition, SqlType, Inserter, TableName


def _infer_sql_type(all_data: list, key: str) -> SqlType:
    """
    Scan ALL rows for a given key to infer the safest Tableau SqlType.
    - If ANY value is a float or Decimal  → double()
    - If ALL non-null values are int only → big_int()
    - If mixed types or any string        → text()
    """
    has_float = False
    has_int = False
    has_str = False

    for row in all_data:
        val = row.get(key)
        if val is None or val == "":
            continue
        if isinstance(val, bool):
            has_str = True
        elif isinstance(val, float) or isinstance(val, Decimal):
            has_float = True
        elif isinstance(val, int):
            has_int = True
        else:
            try:
                float(str(val).replace(',', ''))
                has_float = True
