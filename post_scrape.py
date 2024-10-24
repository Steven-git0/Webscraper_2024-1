#pip3 install psycopg2-binary pandas gremlinpython
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


#psql -h 3.142.242.94 -p 5432 -U steven_y_202311 -d beamdatadwc
postgres_config = {
    "host": '3.142.242.94',
    'user': 'steven_y_202311',
    'password': 'vj2fzefzMW6fVDt1Mo59',
    'database': 'beamdatadwc',
    'port':  '5432'
}

def retrieve_postgres():
    data = []
    try:
        with psycopg2.connect(**postgres_config) as conn:
            with conn.cursor() as cur:
                #do not use distinct page url as you cannot properly make an edge.
                cur.execute("SELECT Distinct page_url, status_code, web_links, date FROM mktg_seo_raw.scrape_staging")
                data = cur.fetchall()
                print('running')
        print('Getting from Database')
        return data
    except Exception as e:
        print(f"Error occurred: {e}")

#for testing purposes
# def create_csv(data):
#     for page_url, _, web_links, date in data:
#         if page_url == 'https://weclouddata.com/success-stories/manny-brar/':
#             print('page url: ', page_url)
#             if web_links:
#                 web_links_list = web_links.strip('{}').split(',')
#                 #For testing the data, making sure the links from a scraped website are in the proper format.
#                 with open('output.csv', 'w', newline='') as csvfile:
#                     writer = csv.writer(csvfile)
#                     for row in web_links_list:
#                         writer.writerow([row.strip()])
#                         print(row)
#                 print(' CSV CREATED')

def sql_broken():
    try:
        with psycopg2.connect(**postgres_config) as conn:
            with conn.cursor() as cur:
                #clear the intermediary table
                cur.execute("""
                    TRUNCATE TABLE mktg_seo_raw.broken_links_temp;
                """)
                #Match existing broken urls from each tables and add new broken links, query will automatically discard fixed links
                cur.execute("""
                    --use staging status code in case in rare case status code is to be changed
                    INSERT INTO mktg_seo_raw.broken_links_temp (date, original_url, status_code)
                    SELECT db1.date, db1.original_url, db2.status_code
                    FROM mktg_seo_raw.broken_links db1
                    --Join the current broken links with the scraped broken links 
                    INNER JOIN mktg_seo_raw.scrape_staging db2 ON db1.original_url = db2.original_url
                    WHERE db2.status_code >= 300
                    --Join new broken links
                    UNION
                    SELECT db2.date, db2.original_url, db2.status_code
                    FROM mktg_seo_raw.scrape_staging db2
                    LEFT JOIN mktg_seo_raw.broken_links db1 ON db2.original_url = db1.original_url
                    WHERE db1.original_url IS NULL AND db2.status_code >= 300;
                """)
                #Clear the current broken links
                cur.execute("TRUNCATE TABLE mktg_seo_raw.broken_links;")
                #import the new data into the existing broken links
                cur.execute("""
                    INSERT INTO mktg_seo_raw.broken_links (date, original_url, status_code)
                    SELECT date, original_url, status_code
                    FROM mktg_seo_raw.broken_links_temp; 
                """)
                print("Broken Links Added")

    except Exception as e:
        print(f"Error occurred: {e}")

#Populate Elements, daily scrape and stores the website data.
def sql_tables():
    try:
        with psycopg2.connect(**postgres_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO mktg_seo_raw.wcd_elements (original_url, redirect, header_tags, meta_data, meta_description, meta_charset, web_links, image_url, image_alt, canonical_url)
                SELECT original_url, redirect, header_tags, meta_data, meta_description, meta_charset, web_links, image_url, image_alt, canonical_url
                FROM mktg_seo_raw.scrape_staging
                """)
                print('Elements Inserted')
                cur.execute("""
                INSERT INTO mktg_seo_raw.daily_scrape (date, original_url, page_url, status_code, load_time)
                SELECT date, original_url, page_url, status_code, load_time
                FROM mktg_seo_raw.scrape_staging
                """)
                print('Daily Scrape inserted')
                cur.execute("""
                INSERT INTO mktg_seo_raw.website_storage
                SELECT *
                FROM mktg_seo_raw.scrape_staging s
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM mktg_seo_raw.website_storage w
                    WHERE w.original_url = s.original_url AND w.date = s.date
                )
                """)
                print('Scraped Data placed in storage')
    except Exception as e:
        print(f"Error occurred: {e}")

#Used in create edges, populate urls database will be made while janusgraph graph is made to save resources
def sql_urls(main, domain, external, anomoly):
    try:
        with psycopg2.connect(**postgres_config) as conn:
            with conn.cursor() as cur:
                #do not use distinct page url as you cannot properly make an edge.
                cur.execute("""
                    INSERT INTO mktg_seo_raw.web_links(original_url, domain_urls, external_urls, anomoly_urls, date)
                    VALUES (%s, %s, %s, %s, %s);
                """, (main, domain, external, anomoly, datetime.datetime.now()))
                cur.execute("""
                    INSERT INTO mktg_seo_raw.web_links_storage(original_url, domain_urls, external_urls, anomoly_urls, date)
                    VALUES (%s, %s, %s, %s, %s);
                """, (main, domain, external, anomoly, datetime.datetime.now()))
                print('URL Data Inserted')
    except Exception as e:
        print(f"Error occurred: {e}")

#Clear the janusgraph
def clear_graph():
    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g',
                                                        message_serializer=GraphSONSerializersV3d0()))
    g.V().drop().iterate()

#Make the verticies
def insert_janusgraph(data):
    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g',
                                                        message_serializer=GraphSONSerializersV3d0()))
    print('Inserting into janusgraph')
    try:
        for page_url, status_code, web_links, date in data:
            date_str = date.strftime('%Y-%m-%d')
            source_vertex = g.V().has('page', 'url', page_url).fold().coalesce(
                __.unfold(),
                __.addV('page').property('url', page_url).property('status_code', status_code).property('date', date_str)
            ).next()

        print('Finished creating Verticies, Creating Edges')
    except Exception as e:
      print(f"An error occurred: {e}")

#Make the edges (conenctions between websites)
def create_edges(data):

    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g',
                                                        message_serializer=GraphSONSerializersV3d0()))

    #create a cache to store verticies for SIGNIFICANTLY FASTER PROCESSING 
    vertex_cache = {}

    for page_url, _, web_links, date in data:
        print('page url: ', page_url)
        #check to make sure the vertex has weblinks
        if web_links:
            #split up weblinks for creating edges
            web_links_list = web_links.strip('{}').split(',')
            #if the current url is not in cache append and set current url as the current vertex
            if page_url not in vertex_cache:
                source_vertex = g.V().has('page', 'url', page_url).next()
                vertex_cache[page_url] = source_vertex
            #else set the url if already in cache as current vertex
            else:
                source_vertex = vertex_cache[page_url]

            sql_domain_urls = []
            sql_external_urls = []
            sql_anomoly_urls = []
            #from the current vertex start iterating through it's web link list 
            for link in web_links_list:
                try:
                    #If link is not in the cache and is in domain link. Get the target vertex and save into cache
                    if link not in vertex_cache and 'https://weclouddata.com/' in link:
                        try:
                            target_vertex = g.V().has('page', 'url', link).next()
                            vertex_cache[link] = target_vertex
                        #In the event the URL does not have a vertex it will save it as an anomoly for manual review
                        except Exception as e:
                            error_message = (f"An error occurred: {type(e).__name__}, {str(e)}")
                            print('Anomoly in Url, Skipping')
                            url_anomoly = (f"{link} {error_message}")
                            g.V(source_vertex).property(Cardinality.list_,'url_anomoly', url_anomoly).iterate()
                            sql_anomoly_urls.append(link)
                            #skips the rest of the loop to the next link
                            continue
                            
                    # save external links
                    elif 'https://weclouddata.com/' not in link:
                        print('external link')
                        external_url = (f"{link}")
                        g.V(source_vertex).property(Cardinality.list_, 'external_url', external_url).iterate()
                        sql_external_urls.append(link)
                    #vertex is in cache
                    else:
                        target_vertex = vertex_cache[link]
                    #create the edge only if in domain url.
                    if 'https://weclouddata.com/' in link:
                        g.addE('links_to').from_(source_vertex).to(target_vertex).iterate()
                        print('creating edge from ', g.V(source_vertex).values('url').next(), ' to ', g.V(target_vertex).values('url').next())
                        sql_domain_urls.append(link)

                except GremlinServerError as e:
                    print(f"Gremlin server error occurred: {type(e).__name__}, {str(e)}")
                    continue
                except DriverRemoteConnectionError as e:
                    print(f"Connection error occurred: {type(e).__name__}, {str(e)}")
                    continue
                except Exception as e:
                    print(f"An error occurred: {type(e).__name__}, {str(e)} ")
                    continue
            #gather all the list and save into weblinks sql table
            sql_urls(page_url, sql_domain_urls, sql_external_urls, sql_anomoly_urls)
        #user_input = input("Press enter to continue ")


#docker run --rm --network janusgraph_web --link janusgraph-server:janusgraph -e GREMLIN_REMOTE_HOSTS=janusgraph  -it janusgraph/janusgraph ./bin/gremlin.sh
#:remote connect tinkerpop.server conf/remote.yaml
#:remote console
#g
#docker exec -it --user root janusgraph-server /bin/bash
#apt-get update && apt-get install nano


print('starting')
print('clearing existing graph')
clear_graph()
print('Retreiving Data')
data = retrieve_postgres()
print('inserting verticies')
insert_janusgraph(data)
print('creating edges')
create_edges(data)
print('updating broken links table')
sql_broken()
print('updating remaining tables')
sql_tables()
