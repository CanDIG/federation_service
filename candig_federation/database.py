import datetime
import sqlite3

CACHE_FLUSH_PERIOD = datetime.timedelta(hours=1)

def get_connection():
    con = sqlite3.connect("cache.db", check_same_thread=False)
    cur = con.cursor()
    return con, cur

def initialize():
    """
    Initialize the sqlite3 database of cached requests
    """
    con, cur = get_connection()

    # Delete any old cache
    cur.execute("DROP TABLE IF EXISTS Cache;")

    # Create a new cache
    cur.execute("CREATE TABLE Cache(hash TINYTEXT PRIMARY KEY, data MEDIUMTEXT, last_access TIMESTAMP)")
    con.commit()

def get_cache(hash):
    """
    Get the given cache entry, if it exists. Does not modify the last_access entry.
    Returns None if it does not exist
    """
    _, cur = get_connection()
    cur.execute("SELECT data FROM Cache WHERE hash=(?)", (hash,))
    res = cur.fetchone()

    # Get the data field if successful
    if res is not None:
        res = res[0]

    return res

def set_cache(hash, data):
    """
    Insert the given cache entry
    """
    con, cur = get_connection()
    cur.execute("INSERT INTO Cache VALUES(?, ?, ?)", (hash, data, datetime.datetime.now()))
    con.commit()

def touch_cache(hash):
    """
    Reset the last_access on the given cache entry
    """
    con, cur = get_connection()
    cur.execute("UPDATE Cache SET last_access=(?) WHERE hash=(?)", (datetime.datetime.now(), hash))
    con.commit()

def flush_cache(period=CACHE_FLUSH_PERIOD):
    """
    Remove all entries in the cache that are older than a certain time period
    """
    con, cur = get_connection()
    cur.execute("DELETE FROM Cache WHERE last_access < (?)", (datetime.datetime.now() - period))
