import sqlite3
from sqlite3 import Error
import os.path as path


class DBConnection:
    def __init__(self, db_file_name):
        # We assume that the database is in the current directory since this
        # is how it's laid out at the moment

        BASE_DIR = path.dirname(path.abspath(__file__))
        full_path = path.join(BASE_DIR, db_file_name)
        print(full_path)
        self.conn = None
        try:
            self.conn = sqlite3.connect(full_path)
        except Error as e:
            print(e)

    def send_query(self, query, params=None):
        # This method will just be used to send queries, it will be changed in
        # the future since different queries require different methods and
        # returns.
        if params is None:
            params = {}
        cur = self.conn.cursor()
        return cur.execute(query, params)
