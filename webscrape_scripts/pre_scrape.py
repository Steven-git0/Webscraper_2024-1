import psycopg2
import pandas as pd
import csv
import time
import datetime
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __, GraphTraversalSource
from gremlin_python.process.traversal import Cardinality
from gremlin_python.process.strategies import *
from gremlin_python.driver.serializer import GraphSONSerializersV3d0

#Janusgraph will be cleared in the post_scrape to save resources 

#psql -h 3.142.242.94 -p 5432 -U steven_y_202311 -d beamdatadwc
postgres_config = {
    "host": '3.142.242.94',
    'user': 'steven_y_202311',
    'password': 'vj2fzefzMW6fVDt1Mo59',
    'database': 'beamdatadwc',
    'port':  '5432'
}

def truncate_tables():
    try:
        with psycopg2.connect(**postgres_config) as conn:
            with conn.cursor() as cur:
                #Clear the staging and temporary tables/databases
                cur.execute('DELETE FROM mktg_seo_raw.scrape_staging')
                cur.execute('DELETE FROM mktg_seo_raw.web_links')
                cur.execute('DELETE FROM mktg_seo_raw.wcd_elements')
                cur.execute('DELETE FROM mktg_seo_raw.daily_scrape')
                print('running')
        print('Staging Database Cleared')
    except Exception as e:
        print(f"Error occurred: {e}")

#scrapy run command: docker run --rm scrapy_project
truncate_tables()