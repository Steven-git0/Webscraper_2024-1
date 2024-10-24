# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from itemadapter import is_item, ItemAdapter
import logging
import time


class TimingMiddleware:
    
    def __init__(self):
        self.stats = {}

    @classmethod
    def from_crawler(cls, crawler):     
        instance = cls()
        #start signal for when scrapy downloader start to retrieve the information
        #IT MUST BE request_reached_downloader, request_scheduled starts the timer it is in queue not when it is retreving it.
        crawler.signals.connect(instance.request_scheduled, signal=signals.request_reached_downloader)
        #end signal for when the html is recieved
        crawler.signals.connect(instance.response_received, signal=signals.response_received)
        return instance

    def request_scheduled(self, request, spider):
        request.meta['start_time'] = self.current_time()
        
    def response_received(self, response, request, spider):
        end_time = self.current_time()
        start_time = request.meta.get('start_time')
        if start_time:
            load_time = end_time - start_time
            response.meta['load_time'] = load_time  # Pass the load time via response.meta
            logging.debug(f"Load time for {request.url}: {response.meta['load_time']}")
            logging.debug(f"Start time for {request.url}: {request.meta['start_time']}") 
            logging.debug(f"Endtime for {request.url}: {end_time}")
        return response

    def current_time(self):
        #time.time() also works for lower defintion
        return time.perf_counter()

