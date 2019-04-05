# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl colspider -t csv -o - > colspider.csv
"""
import os
import scrapy
from scrapy.http.request import Request
from legis.items import ColspiderItem

class ColspiderSpider(scrapy.Spider):
    name = 'colspider'
    allowed_domains = ['leg.colorado.gov']
    start_urls = ['http://leg.colorado.gov/content/committees']

    def parse(self, response):
        i = -1
        for n in response.xpath('//span[@class="field-content"]/a/@href').extract():
            i += 1
            if n is not None:
                yield Request(response.urljoin(n), callback=self.parsefiles, meta={'cat': response.xpath('//span[@class="field-content"]/a/text()').extract()[i]})

    def parsefiles(self, response):
        for n in response.xpath('//td[@class="committee-activity-documents"]/a[contains(text(),"Hearing Summary Document")]/@href').extract():
            yield Request(response.urljoin(n), callback=self.parsesave, meta=response.meta )

    def parsesave(self, response):
        filename = './colorado/session/' + response.meta.get('cat') + '-' + response.url.split('/')[-1] + '.htm'
        os.makedirs('./colorado/session/', exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.body)
        yield ColspiderItem(url=response.url)