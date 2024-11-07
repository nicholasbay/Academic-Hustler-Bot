from os import getenv

from dotenv import load_dotenv
import sqlite3


def connect_to_database() -> sqlite3.Connection:
    """
    Connects to the database. Creates the database if it doesn't exist.

    Returns:
        sqlite3.Connection: The connection object.
    """
    load_dotenv()
    DB_PATH = getenv('DB_PATH')

    return sqlite3.connect(DB_PATH)


def execute_query(query: str,
                  params: tuple = None,
                  fetch: bool = False,
                  fetch_lastrowid: bool = False) -> list | None:
    """
    Executes a SQL query with optional parameters.

    Args:
        query (str): The SQL query.
        params (tuple, optional): Parameters to bind to the query. Defaults to None.
        fetch (bool, optional): Whether to fetch and return results. Defaults to False.
        fetch_lastrowid (bool, optional): Whether to fetch and return last inserted row ID. Defaults to False.

    Returns:
         list: A list of tuples containing the query results if fetch=True.
    """
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()

        if fetch:
            return cursor.fetchall()
        elif fetch_lastrowid:
            return cursor.lastrowid
        else:
            return None

    except sqlite3.Error as e:
        # TODO: Log error
        return None

    finally:
        conn.close()
