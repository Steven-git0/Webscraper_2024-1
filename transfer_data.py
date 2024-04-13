#pip3 install psycopg2-binary pandas gremlinpython
import psycopg2
import pandas as pd
import csv
import time
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
                cur.execute("SELECT Distinct page_url, status_code, web_links, date FROM mktg_seo_raw.wcd_website")
                data = cur.fetchall()
                print('running')
        print('Getting from Database')
        return data
    except Exception as e:
        print(f"Error occurred: {e}")

#for testing purposes
def create_csv(data):
    for page_url, _, web_links, date in data:
        if page_url == 'https://weclouddata.com/success-stories/manny-brar/':
            print('page url: ', page_url)
            if web_links:
                web_links_list = web_links.strip('{}').split(',')
                #For testing the data, making sure the links from a scraped website are in the proper format.
                with open('output.csv', 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    for row in web_links_list:
                        writer.writerow([row.strip()])
                        print(row)
                print(' CSV CREATED')

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
#Make the edges
def create_edges(data):

    graph = Graph()
    g = graph.traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g',
                                                        message_serializer=GraphSONSerializersV3d0()))

    #create a cache to store verticies for SIGNIFICANTLY FASTER PROCESSING 
    vertex_cache = {}

    for page_url, _, web_links, date in data:
        print('page url: ', page_url)

        if web_links:
            
            web_links_list = web_links.strip('{}').split(',')

            if page_url not in vertex_cache:
                source_vertex = g.V().has('page', 'url', page_url).next()
                vertex_cache[page_url] = source_vertex
            else:
                source_vertex = vertex_cache[page_url]
            
            #Unable to add cardinality to vertex values, saving to list and adding at end as an alternative solution
            url_anomoly = []
            external_url = []

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
                            url_anomoly.append(f"{link} {error_message}")
                            #skips the rest of the loop to the next link
                            continue
                            
                    # save external links
                    elif 'https://weclouddata.com/' not in link:
                        print('external link')
                        external_url.append(f"{link}")
                    #vertex is in cache
                    else:
                        target_vertex = vertex_cache[link]
                    #create the edge only if in domain url.
                    if 'https://weclouddata.com/' in link:
                        g.addE('links_to').from_(source_vertex).to(target_vertex).iterate()
                        print('creating edge from ', g.V(source_vertex).values('url').next(), ' to ', g.V(target_vertex).values('url').next())

                except GremlinServerError as e:
                    print(f"Gremlin server error occurred: {type(e).__name__}, {str(e)}")
                    continue
                except DriverRemoteConnectionError as e:
                    print(f"Connection error occurred: {type(e).__name__}, {str(e)}")
                    continue
                except Exception as e:
                    print(f"An error occurred: {type(e).__name__}, {str(e)} ")
                    continue
            #insert found external links, unproccessable urls into the vertex
            g.V(source_vertex).property('url_anomoly', url_anomoly).iterate()
            g.V(source_vertex).property('external_url', external_url).iterate()

        #user_input = input("Press enter to continue ")



#docker run --rm --network janusgraph_web --link janusgraph-server:janusgraph -e GREMLIN_REMOTE_HOSTS=janusgraph  -it janusgraph/janusgraph ./bin/gremlin.sh
#:remote connect tinkerpop.server conf/remote.yaml
#:remote console
#docker exec -it --user root janusgraph-server /bin/bash
#apt-get update && apt-get install nano

print('starting')
data = retrieve_postgres()
print('inserting verticies')
insert_janusgraph(data)
print('creating edges')
create_edges(data)

