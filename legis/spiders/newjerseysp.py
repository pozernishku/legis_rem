# -*- coding: utf-8 -*-
# Run: scrapy crawl newjersey -s LOG_FILE=scrapy_newjersey.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=32 -s DOWNLOAD_DELAY=2
import scrapy
import pandas as pd
import os
import io
from urllib.request import urlopen
import time
from scrapy.http.request import Request
from scrapy.selector import Selector


class NewjerseyspSpider(scrapy.Spider):
    name = 'newjerseysp'
    allowed_domains = ['www.njleg.state.nj.us']
    start_urls = ['http://www.njleg.state.nj.us/']

    def parse(self, response):
        newjersey_csv = pd.read_csv('./params/njleg_20170904.csv', index_col = 1)

        for i in range(newjersey_csv.url.count()):
            yield response.follow(newjersey_csv.url[[i]][0], callback=self.parse_next)
            
    def parse_next(self, response):
        filename = response.url.split('/')[-1]
        os.makedirs('./pdfs/', exist_ok=True)
        with open('./pdfs/' + filename, 'wb') as f:
            f.write(response.body)