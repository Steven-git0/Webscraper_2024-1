#scrapy crawl wcdspider -O wcd1.csv
import scrapy
import IPython
import re
import datetime
import sys
import time

from pathlib import Path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))
from items import WcdscrapeItem


class webSpider(scrapy.Spider):
    name = "wcdspider"
    allowed_domains = ["weclouddata.com"]
    start_urls = ["https://weclouddata.com/"]

    custom_settings = {
        'FEEDS': {
            'wcd1.csv': {'format': 'csv', 'overwrite': True},
        }
    }

    def normalize_url(self, link):
        main_url = 'https://weclouddata.com'
        #often links don't have the full url and only the branch ending and ending /. This to prevent duplicate urls from being scanned.
        if not link.startswith(('http://', 'https://')):
            link = main_url + link
        if not link.endswith('/'):
            link += '/'
        return link

    def parse(self, response):

        #print("Fields in the item:", list(WcdscrapeItem.fields.keys()))
        wcd_item = WcdscrapeItem()
        
        wcd_item['date'] = datetime.datetime.now()
        wcd_item['original_url'] = response.request.url
        wcd_item['page_url'] = response.url
        wcd_item['redirect'] = False if wcd_item['original_url'] == wcd_item['page_url'] else True
        wcd_item['status_code'] = response.status
        wcd_item['meta_data'] = [{'name': meta.xpath('@name').get() or meta.xpath('@property').get(),
                                  'content': meta.xpath('@content').get()} for meta in response.css('meta')]
        meta_description = response.css('meta[name="description"]::attr(content)').getall()
        wcd_item['meta_description'] = meta_description if meta_description  else 'N/A'
        wcd_item['meta_charset'] = response.xpath('//meta[@charset]/@charset').get()
        wcd_item['header_tags'] = response.css('h1::text, h2::text, h3::text, h3.elementor-post__title a::text').getall() #, h4::text, h5::text, h6::text
        #retrieve all links and exludes emails and self references 
        wcd_item['web_links'] = [href for href in response.css('a::attr(href)').getall() 
                                    if not any(substring in href for substring in ['@', '#', '#content'])]
        #loops through and normalize all the urls and remove duplicates
        seen = set()
        #Python 3.8 is needed for := as it called the function once and set it as a variable
        wcd_item['web_links'] = [normalized_link for link in wcd_item['web_links']
                         if (normalized_link := self.normalize_url(link)) not in seen and not seen.add(normalized_link)]

        wcd_item['image_url'] = response.css('img::attr(src)').getall()
        wcd_item['image_alt'] = response.css('img::attr(alt)').getall()#image description

        wcd_item['canonical_url'] = response.xpath("//link[@rel='canonical']/@href").getall()

        wcd_item['load_time'] = response.meta.get('load_time')


        yield wcd_item
        
        #Will scan through every link of a website and check if it has scraped it, if not it will scrape
        for link in wcd_item['web_links']:
            absolute_url = response.urljoin(link) 
            print(f'Going to new Link: {absolute_url}')
            yield scrapy.Request(url = absolute_url, callback = self.parse, errback = self.handle_error)
    
    def handle_error(self, failure):
        wcd_item = WcdscrapeItem()
        wcd_item['date'] = datetime.datetime.now()
        wcd_item['original_url'] = failure.request.url
        if hasattr(failure.value, 'response'):
            response = failure.value.response
            wcd_item['page_url'] = response.url
            wcd_item['status_code'] = response.status
        else:
            wcd_item['page_url'] = 'No response'
            wcd_item['status_code'] = 'No response'
        
        yield wcd_item
    


