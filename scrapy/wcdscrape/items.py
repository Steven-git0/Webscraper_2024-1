# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

#example serializer to use set any variable = function in .Field()
# def lowercase(value):
#     value = str(value)
#     return value.lower()

class WcdscrapeItem(scrapy.Item):

    date = scrapy.Field()
    original_url = scrapy.Field()
    page_url = scrapy.Field()
    redirect = scrapy.Field()
    status_code = scrapy.Field()
    header_tags = scrapy.Field()
    meta_data = scrapy.Field()
    meta_description = scrapy.Field()
    meta_charset = scrapy.Field()
    web_links = scrapy.Field()
    image_url = scrapy.Field()
    image_alt = scrapy.Field()
    canonical_url = scrapy.Field()
    load_time = scrapy.Field()



        