import sqlite3
from sqlite3 import Error
import os.path as path


def init_connection(db_file_name):
    # We assume that the database is in the current directory since this is how
    # it's laid out at the moment
    full_path = path.realpath(db_file_name)

    conn = None

    try:
        conn = sqlite3.connect(full_path)
    except Error as e:
        print(e)

    return conn


# This method will just be used to send queries, it will be changed in the
# future since different queries require different methods and returns.
def send_query(conn, query):
    cur = conn.cursor()

    cur.execute(query)


def main():
    conn = init_connection('AKODatabase.db')


if __name__ == "__main__":
    main()
