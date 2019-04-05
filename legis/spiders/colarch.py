# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl colarch -t csv -o - > colarch.csv
"""
import os
import scrapy
from scrapy.http.request import Request
from legis.items import ColarchItem

class ColarchSpider(scrapy.Spider):
    name = 'colarch'
    allowed_domains = ['leg.state.co.us']
    start_urls = [
        #change the year in link below. For 2006, 2004, 2005, 2004 use shorter link
        'http://www.leg.state.co.us/CLICS2004A/commsumm.nsf/CommByBillSumm?OpenView&Start=1&Count=500&ExpandView'
        #'http://www.leg.state.co.us/CLICS/CLICS2007A/commsumm.nsf/CommByBillSumm?OpenView&Start=1&Count=500&ExpandView'
        ]
    numb = -1
    def parse(self, response):
        for n in response.xpath('//a[contains(text(),"Bill Summary")]/@href').extract():
            self.numb += 1
            if n is not None: 
                yield Request(response.urljoin(n), callback=self.parsefiles, meta={'numb': self.numb})

        next_page = response.xpath('//a[contains(text(),"Next")]/@href').extract_first()
        if response.url.split('&')[-3] != response.xpath('//a[contains(text(),"Next")]/@href').extract_first().split('&')[-3]:
            next_page = response.urljoin(next_page)
            yield Request(next_page, callback=self.parse)

    def parsefiles(self, response):
        y = response.url[32:36] if '20' in response.url[32:36] else ''
        p = ''.join(response.xpath('/html/body/form/div[1]/font[4]/text() | /html/body/form/div[1]/font[5]/text() | /html/body/form/div[1]/font[6]/text() | /html/body/form/div[1]/font[7]/text() | /html/body/form/div[1]/font[8]/text()').extract()) if '20' in response.url[32:36] else ''.join(response.xpath('/html/body/div[1]/font[4]/text() | /html/body/div[1]/font[5]/text() | /html/body/div[1]/font[6]/text() | /html/body/div[1]/font[7]/text() | /html/body/div[1]/font[8]/text()').extract())
        f = (response.xpath('/html/body/form/div[1]/font[3]/text()').extract_first() if response.xpath('/html/body/form/div[1]/font[3]/text()').extract_first() is not None else 'No Bill Number').replace('/', '-') if '20' in response.url[32:36] else (response.xpath('/html/body/div[1]/font[3]/text()').extract_first() if response.xpath('/html/body/div[1]/font[3]/text()').extract_first() is not None else 'No Bill Number').replace('/', '-')
        
        filename = './colorado/archive/' + f + ' ' + p + ' ' + (response.xpath('/html/body/font[2]/text()').extract_first().replace('/', '-') if response.xpath('/html/body/font[2]/text()').extract_first() is not None else y) + ' ' + str(response.meta.get('numb')) + '.htm'
        os.makedirs('./colorado/archive/', exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.body)
        yield ColarchItem(url=response.url)
