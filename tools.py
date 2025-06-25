import json
import os
import sqlite3
from typing import Tuple, Optional

from smolagents import tool


@tool
def list_data_sources() -> list[dict]:
    """List all available data sources.

    Returns:
        list[dict]: List of dicts containing info for each data source (name, description, type, etc.)
    """
    data_sources_path = "data_sources"
    data_sources: list[dict] = []

    if not os.path.exists(data_sources_path):
        return data_sources

    for item in os.listdir(data_sources_path):
        item_path = os.path.join(data_sources_path, item)
        if os.path.isdir(item_path):
            info_json_path = os.path.join(item_path, "info.json")
            if os.path.exists(info_json_path):
                try:
                    with open(info_json_path, 'r') as f:
                        info_data = {"name": item}
                        info_data.update(json.load(f))
                        data_sources.append(info_data)
                except (json.JSONDecodeError, IOError):
                    continue

    return data_sources


def _load_data_source_info(data_source_name: str) -> Tuple[Optional[dict], Optional[str]]:
    """Load info.json for a data source.

    Args:
        data_source_name (str): Name of the data source

    Returns:
        Tuple[Optional[dict], Optional[str]]: (info_data, error_message)
    """
    data_sources_path = "data_sources"
    info_json_path = os.path.join(data_sources_path, data_source_name, "info.json")

    # Check if info.json exists
    if not os.path.exists(info_json_path):
        return (
            None,
            f"Error: Data source '{data_source_name}' not found. The info.json file does not exist at path: {info_json_path}",
        )

    try:
        # Read info.json to get database info
        with open(info_json_path, 'r') as f:
            info_data = json.load(f)
        return info_data, None
    except json.JSONDecodeError as e:
        return (
            None,
            f"Error: Invalid JSON format in info.json for data source '{data_source_name}'. JSON decode error: {str(e)}",
        )
    except IOError as e:
        return None, f"Error: Could not read info.json for data source '{data_source_name}'. IO error: {str(e)}"


def _get_sqlite_db_path(data_source_name: str, info_data: dict) -> Tuple[Optional[str], Optional[str]]:
    """Get the SQLite database path from data source info.

    Args:
        data_source_name (str): Name of the data source
        info_data (dict): Data source info from info.json

    Returns:
        Tuple[Optional[str], Optional[str]]: (db_path, error_message)
    """
    # Check if it's a SQLite database
    if info_data.get("type") != "SQLite":
        return (
            None,
            f"Error: Data source '{data_source_name}' is not a SQLite database. Type is: {info_data.get('type', 'unknown')}",
        )

    # Get database file path
    db_file = info_data.get("file")
    if not db_file:
        return (
            None,
            f"Error: No database file specified in info.json for data source '{data_source_name}'. Expected 'file' field is missing.",
        )

    data_sources_path = "data_sources"
    db_path = os.path.join(data_sources_path, data_source_name, db_file)

    # Check if database file exists
    if not os.path.exists(db_path):
        return None, f"Error: SQLite database file not found at path: {db_path}"

    return db_path, None


@tool
def describe_data_source(data_source_name: str) -> str:
    """Get the description of a given data source. It's mandatory to read it before querying the data source.

    Args:
        data_source_name (str): Name of the data source

    Returns:
        str: Description of the data source or an error message if not found
    """
    data_sources_path = "data_sources"
    readme_path = os.path.join(data_sources_path, data_source_name, "README.md")

    if not os.path.exists(readme_path):
        return ""

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError:
        return ""


@tool
def sqlite_get_schema(data_source_name: str) -> str:
    """Get the database schema of a SQLite data source.

    Args:
        data_source_name (str): Name of the data source

    Returns:
        str: SQLite schema or error description
    """
    # Load data source info
    info_data, error = _load_data_source_info(data_source_name)
    if error:
        return error

    # Get database path
    db_path, error = _get_sqlite_db_path(data_source_name, info_data)
    if error:
        return error

    try:
        # Connect to database and get schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table schemas
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL ORDER BY name;")
        table_schemas = cursor.fetchall()

        # Get all view schemas
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND sql IS NOT NULL ORDER BY name;")
        view_schemas = cursor.fetchall()

        conn.close()

        # Format the schema
        schema_parts = []

        if table_schemas:
            schema_parts.append("-- Tables")
            for schema in table_schemas:
                schema_parts.append(schema[0] + ";")

        if view_schemas:
            schema_parts.append("\n-- Views")
            for schema in view_schemas:
                schema_parts.append(schema[0] + ";")

        if not schema_parts:
            return f"Warning: SQLite database '{data_source_name}' exists but contains no tables or views."

        return "\n".join(schema_parts)

    except sqlite3.Error as e:
        return f"Error: SQLite database error when accessing '{data_source_name}' at {db_path}. SQLite error: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error when processing SQLite database '{data_source_name}'. Error: {str(e)}"


@tool
def sqlite_query(data_source_name: str, sql_query: str) -> str:
    """Execute a SQL query against a SQLite data source.

    Args:
        data_source_name (str): Name of the data source
        sql_query (str): SQL query to execute

    Returns:
        str: Query results formatted as string or error description
    """
    # Load data source info
    info_data, error = _load_data_source_info(data_source_name)
    if error:
        return error

    # Get database path
    db_path, error = _get_sqlite_db_path(data_source_name, info_data)
    if error:
        return error

    # Validate SQL query is not empty
    if not sql_query.strip():
        return "Error: SQL query cannot be empty."

    try:
        # Connect to database and execute query
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(sql_query)

        # Check if it's a SELECT query (returns results)
        query_type = sql_query.strip().upper().split()[0]

        if query_type == "SELECT":
            # Fetch results for SELECT queries
            results = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]

            if not results:
                conn.close()
                return "Query executed successfully but returned no results."

            # Format results as a table-like string
            result_lines = []
            result_lines.append(" | ".join(column_names))
            result_lines.append("-" * len(result_lines[0]))

            for row in results:
                formatted_row = []
                for value in row:
                    if value is None:
                        formatted_row.append("NULL")
                    else:
                        formatted_row.append(str(value))
                result_lines.append(" | ".join(formatted_row))

            conn.close()
            return "\n".join(result_lines)
        else:
            # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            return f"Query executed successfully. Rows affected: {rows_affected}"

    except sqlite3.Error as e:
        return f"Error: SQLite error when executing query on '{data_source_name}'. SQLite error: {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error when executing query on '{data_source_name}'. Error: {str(e)}"
