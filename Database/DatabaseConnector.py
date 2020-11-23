import sqlite3
from sqlite3 import Error
import os.path as path

def initConnection(dbFileName):
    
    # We assume that the database is in the current directory since this is how it's laid out at the moment
    fullPath = path.realpath(dbFileName)
    
    conn = None
    
    try:
        conn = sqlite3.connect(fullPath)
    except Error as e:
        print(e)

    return conn

# This method will just be used to send queries, it will be changed in the future since different queries require different
# methods and returns.
def sendQuery(conn, query):
    cur = conn.cursor()
    
    cur.execute(query)

def main():
    conn = initConnection('AKODatabase.db')

if __name__ == "__main__":
    main()