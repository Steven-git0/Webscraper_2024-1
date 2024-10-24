# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re 
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import logging
import psycopg2
import csv
import io


class WcdscrapePipeline:
    
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)
        meta_data = adapter.get('meta_data')

        if meta_data:
            output = io.StringIO()
            csv_convert = csv.DictWriter(output, fieldnames = meta_data[0].keys())
            csv_convert.writeheader
            csv_convert.writerows(meta_data)

            csv_meta_data = output.getvalue()
            output.close()

            adapter['meta_data'] = csv_meta_data
        
        return item
    
    # def process_url(self, item, spider):
    #      adapter = ItemAdapter
    #      if adapter.get()
    
    # def process_weblinks(self, item, spider):
    #     #Some hrefs do not contain the main url and must be added eg. "href = '/courses"
    #     #alternativley removing the main url would save more space, as long as the context is carried forward
    #     adapter = ItemAdapter(item)
    #     if adapter.get('web_links'):
    #         main_url = 'https://weclouddata.com'
    #         append_url = [(main_url + link if not link.startswith(('http://', 'https://')) else link) +
    #                       ('/' if link.endswith(('/')) else '') for link in adapter['web_links']]
    #         adapter['web_links'] = append_url
    #     return item

class SaveToPostgresSQL(object):
    def __init__(self):
        self.create_connection()
    
    def create_connection(self):
        try:
            self.connection = psycopg2.connect(
                host = '3.142.242.94',
                user = 'steven_y_202311',
                password = 'vj2fzefzMW6fVDt1Mo59',
                database = 'beamdatadwc',
                port = '5432'
            )
            self.curr = self.connection.cursor()
        except psycopg2.DatabaseError as e:
                raise DropItem(f"Database connection error: {e}")

        # self.curr.execute("""
        # CREATE TABLE IF NOT EXISTS mktg_seo_raw.WCD_WEBSITE1(
        #     original_url varchar(50),
        #     date varchar(50)
        # )
        # """)
    
    def process_item(self, item, spider):
        self.store_db(item)
        return item
    
    def store_db(self, item):
        try:
            self.curr.execute(""" 
                INSERT INTO mktg_seo_raw.scrape_staging
                (date, original_url, page_url, redirect, status_code, meta_data, meta_description, meta_charset, header_tags, web_links, image_url, image_alt, canonical_url, load_time) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            item.get('date'),
            item.get('original_url'),
            item.get('page_url'),
            item.get('redirect'),
            item.get('status_code'),
            item.get('meta_data'),
            item.get('meta_description'),
            item.get('meta_charset'),
            item.get('header_tags'),
            item.get('web_links'),
            item.get('image_url'),
            item.get('image_alt'),
            item.get('canonical_url'),
            item.get('load_time')
            ))
            self.connection.commit()

        except psycopg2.DatabaseError as e:
                self.connection.rollback()
                raise DropItem(f"Error saving item to database: {e}")
        
    def close_spider(self, spider):
            self.curr.close()
            self.connection.close()



# CREATE TABLE mktg_seo_raw.wcd_website2 (
#     date DATE,
#     original_url VARCHAR(255) PRIMARY KEY,
#     page_url VARCHAR(255),
#     redirect BOOLEAN,
#     status_code INTEGER,
#     header_tags TEXT,
#     meta_data TEXT,
#     meta_description TEXT,
#     meta_charset VARCHAR(255),
#     web_links TEXT,
#     image_url TEXT,
#     image_alt TEXT,
#     canonical_url VARCHAR(255),
#     load_time FLOAT
# );