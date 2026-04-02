#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Optional

from duckdb_binary import (
    set_db_path as _set_db_path,
    get_db_path as _get_db_path,
    execute_sql as _execute_sql,
    explain_query as _explain_query,
    profile_query as _profile_query,
    list_catalog as _list_catalog,
    get_table_columns as _get_table_columns,
)

_db_path: Optional[Path] = None


def set_db_path(path: str) -> str:
    global _db_path
    _db_path = Path(path)
    return _set_db_path(path)


def get_db_path() -> str:
    return _get_db_path()


def execute_sql(query: str):
    return _execute_sql(query)


def explain_query(query: str, config_overrides=None, set_commands=None):
    return _explain_query(query, config_overrides=config_overrides, set_commands=set_commands)


def profile_query(query: str, config_overrides=None, set_commands=None):
    return _profile_query(query, config_overrides=config_overrides, set_commands=set_commands)


def list_catalog():
    return _list_catalog()


def get_table_columns(schema_name: str, table_name: str):
    return _get_table_columns(schema_name, table_name)