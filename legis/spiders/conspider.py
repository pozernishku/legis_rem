# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl conspider -t csv -o - > conspider.csv
"""
import os
import scrapy
from scrapy.http.request import Request
from legis.items import ConspiderItem


class ConspiderSpider(scrapy.Spider):
    name = 'conspider' 
    allowed_domains = ['search.cga.state.ct.us']

    def start_requests(self):
        urls = [ # year until 2030
            'http://search.cga.state.ct.us/r/adv/dtsearch.asp?posted=posted&name=&number=&numberconn=and&titleopt=phrase&title=&titleconn=and&requestopt=phrase&request=&year1={0}&selectItemyear1={0}&numres=2000&sort=name&sortorder=ascend&stemming=1&getmore=1&db=JFR&posted=posted&submit1='.format(year)
            for year in range(2000, 2031)
        ]
        for url in urls:
            yield Request(url, meta={'download_timeout': 3000, 'max_retry_times': 15} )

    def parse(self, response):
        i = -1
        for n in response.xpath('//td[6]/a/@href').extract():
            i = i + 1
            if n is not None:
                yield Request(n, callback=self.parsefiles, meta={'docname': response.xpath('//td[6]/a/text()').extract()[i]})

    def parsefiles(self, response):
        filename = response.meta.get('docname')
        os.makedirs('./connecticut/', exist_ok=True)
        with open('./connecticut/' + filename, 'wb') as f:
            f.write(response.body)
        yield ConspiderItem(url=response.url)