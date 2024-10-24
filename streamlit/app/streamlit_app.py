import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import time
import psycopg2

from datetime import datetime
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import __, GraphTraversalSource
from gremlin_python.process.strategies import *
from gremlin_python.driver.serializer import GraphSONSerializersV3d0
# Example connection string, adjust the IP and port to your JanusGraph server
graph = Graph()
connection_string = 'ws://3.22.55.181:8182/gremlin'
g = graph.traversal().withRemote(DriverRemoteConnection(connection_string,'g',
                                                    message_serializer=GraphSONSerializersV3d0()))

#access database
postgres_config = {
    "host": '3.142.242.94',
    'user': 'steven_y_202311',
    'password': 'vj2fzefzMW6fVDt1Mo59',
    'database': 'beamdatadwc',
    'port':  '5432'
}

"""
# Welcome to Streamlit!

Edit `/streamlit_app.py` to customize this app to your heart's desire :heart:.
If you have any questions, checkout our [documentation](https://docs.streamlit.io) and [community
forums](https://discuss.streamlit.io).

PLEASE READ:

The first 2 buttons import data into daily_scrape staging and streamlit_staging. 
Both are identical in terms of tables and datatypes, but scrape_staging is the main staging table for the webscraper
streamlit_staging is only used for streamlit. 
"""

# num_points = st.slider("Number of points in spiral", 1, 10000, 1100)
# num_turns = st.slider("Number of turns in spiral", 1, 300, 31)

# indices = np.linspace(0, 1, num_points)
# theta = 2 * np.pi * num_turns * indices
# radius = indices

# x = radius * np.cos(theta)
# y = radius * np.sin(theta)

# df = pd.DataFrame({
#     "x": x,
#     "y": y,
#     "idx": indices,
#     "rand": np.random.randn(num_points),
# })

# st.altair_chart(alt.Chart(df, height=700, width=700)
#     .mark_point(filled=True)
#     .encode(
#         x=alt.X("x", axis=None),
#         y=alt.Y("y", axis=None),
#         color=alt.Color("idx", legend=None, scale=alt.Scale()),
#         size=alt.Size("rand", legend=None, scale=alt.Scale(range=[1, 150])),
#     ))

#finds broken links
def broken_finder(target_url):
    connection = psycopg2.connect(**postgres_config)
    cursor = connection.cursor()
    cursor.execute("SELECT original_url, web_links FROM mktg_seo_raw.scrape_staging")
    
    sql_data = cursor.fetchall()

    cursor.close()
    connection.close()

    processed_data = [(original_url, web_links.split(',')) for original_url, web_links in sql_data if web_links]
    st.write('**Urls with this Broken Link:**', target_url)
    #current urls with broken link
    current_wblink = [original_url for original_url, web_links in processed_data if target_url in web_links] 
    for links in current_wblink:
        st.write(links)

col1, col2 = st.columns(2)

with col1:
    current_date = datetime.now()
    format_date = current_date.strftime("%Y-%m-%d")

    st.title('JanusGraph Map')
    query_date = st.text_input('Enter your date YYYY-MM-DD (Include Dashes)', format_date)

    if st.button('Import Data to scrape_staging'):
        try:
            with psycopg2.connect(**postgres_config) as conn:
                with conn.cursor() as cur:
                    #do not use distinct page url as you cannot properly make an edge.
                    cur.execute(f" INSERT INTO mktg_seo_raw.scrape_staging SELECT * FROM mktg_seo_raw.scrape_staging WHERE date = {query_date}")
                    print('running')
            print('Getting from Database')
        except Exception as e:
            print(f"Error occurred: {e}")

    query_input = st.text_input('Enter your specific url', key = 'input1', placeholder = 'https://weclouddata.com/')
    # Button to execute the count query
    if st.button('Execute Traversal'):
        try:
            # Execute the count() query and fetch the result
            vertex_id = g.V().has('page', 'url', query_input).next()
            vertex_value = g.V(vertex_id).valueMap(True).toList()
            vertex_edges = g.V(vertex_id).outE().inV().values('url').toList()

            date_value = vertex_value[0].get('date',[])
            st.write("**Date:**", date_value)

            status_code = vertex_value[0].get('status_code', [])
            st.write('**Status Code:**', status_code)

            if status_code[0] >= 400:
                broken_finder(query_input)
            else:
                external_urls = vertex_value[0].get('external_url', [])
                st.write('**External Urls**', external_urls)

                anomoly_urls = vertex_value[0].get('url_anomoly', [])
                st.write('**Anomoly Urls:**', anomoly_urls)

                connection = psycopg2.connect(**postgres_config)
                cursor = connection.cursor()
                cursor.execute("SELECT original_url FROM mktg_seo_raw.broken_links")
                
                sql_data = cursor.fetchall()
                broken_urls = [row[0] for row in sql_data]

                cursor.close()
                connection.close()

                #blinks stand for broken links
                current_broken = [present_blinks for present_blinks in vertex_edges if present_blinks in broken_urls]
                
                st.write('**Broken URLs on this Page:**')
                if current_broken:
                    for url in current_broken:
                        st.text(url)
                else:
                    st.write("No Broken Urls!")

                if vertex_edges:
                        st.write('**Outgoing URLs:**')
                        for url in vertex_edges:
                            st.text(url)
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")

with col2:
    st.title('Comparison Map')
    query_date2 = st.text_input('Enter your date YYYY-MM-DD (Include Dashes)', '2024-04-30')

    if st.button('Import Data to streamlit_staging'):
        try:
            with psycopg2.connect(**postgres_config) as conn:
                with conn.cursor() as cur:
                    #do not use distinct page url as you cannot properly make an edge.
                    cur.execute(f" INSERT INTO mktg_seo_raw.scrape_staging SELECT * FROM mktg_seo_raw.scrape_staging WHERE date = {query_date}")
                    print('running')
            print('Getting from Database')
        except Exception as e:
            print(f"Error occurred: {e}")

    query_input = st.text_input('Enter your specific url', key = 'input2', placeholder = 'https://weclouddata.com/')
    # Button to execute the count query
    if st.button('Execute Comparison'):
        try:
            # Execute the count() query and fetch the result
            vertex_id = g.V().has('page', 'url', query_input).next()
            vertex_value = g.V(vertex_id).valueMap(True).toList()
            vertex_edges = g.V(vertex_id).outE().inV().values('url').toList()

            date_value = vertex_value[0].get('date',[])
            st.write("**Date:**", date_value)

            status_code = vertex_value[0].get('status_code', [])
            st.write('**Status Code:**', status_code)

            if status_code[0] >= 400:
                broken_finder(query_input)
            else:
                external_urls = vertex_value[0].get('external_url', [])
                st.write('**External Urls**', external_urls)

                anomoly_urls = vertex_value[0].get('url_anomoly', [])
                st.write('**Anomoly Urls:**', anomoly_urls)

                connection = psycopg2.connect(**postgres_config)
                cursor = connection.cursor()
                cursor.execute("SELECT original_url FROM mktg_seo_raw.broken_links")
                
                sql_data = cursor.fetchall()
                broken_urls = [row[0] for row in sql_data]

                cursor.close()
                connection.close()

                #blinks stand for broken links
                current_broken = [present_blinks for present_blinks in vertex_edges if present_blinks in broken_urls]
                
                st.write('**Broken URLs on this Page:**')
                if current_broken:
                    for url in current_broken:
                        st.text(url)
                else:
                    st.write("No Broken Urls!")

                if vertex_edges:
                        st.write('**Outgoing URLs:**')
                        for url in vertex_edges:
                            st.text(url)
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")