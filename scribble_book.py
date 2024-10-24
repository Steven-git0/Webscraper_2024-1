#for testing not essential for code
import psycopg2
import logging

try:
    logging.debug("Attempting to connect to the database")
    conn = psycopg2.connect(
        host="3.142.242.94",
        database="beamdatadwc",
        user="steven_y_202311",
        password="vj2fzefzMW6fVDt1Mo59",
        port="5432",
        connect_timeout = 10
    )
    logging.debug("Connected successfully")
except Exception as e:
    logging.error("Unable to connect to the database:")
    logging.error(e)
finally:
    if conn is not None:
        conn.close()
        logging.debug("Database connection closed.")

