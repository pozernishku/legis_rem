# -*- coding: utf-8 -*-
# Run: scrapy crawl oregonsp -s LOG_FILE=scrapy_oregon.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=32 -s DOWNLOAD_DELAY=2
import scrapy
import pandas as pd
import os
import io
from urllib.request import urlopen
import time
from scrapy.http.request import Request
from scrapy.selector import Selector

class OregonspSpider(scrapy.Spider):
    name = 'oregonsp'
    allowed_domains = ['olis.leg.state.or.us']
    start_urls = ['https://olis.leg.state.or.us/']

    def parse(self, response):
        oregon_csv = pd.read_csv('./params/oregon_20170904.csv', index_col = 1)[19900:] # change the list len

        for i in range(oregon_csv.url.count()):
            yield response.follow(oregon_csv.url[[i]][0], callback=self.parse_next)
            
    def parse_next(self, response):
        filename = 'CommitteeMeetingDocument_' + response.url.split('/')[-1] + '.pdf'
        os.makedirs('./pdfs/', exist_ok=True)
        with open('./pdfs/' + filename, 'wb') as f:
            f.write(response.body)