# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl ohiopdf -t csv -o - > ohiopdf.csv
"""
import os
import scrapy
from scrapy.http.request import Request
from scrapy.selector import Selector
from legis.items import OhiopdfItem

class OhiopdfSpider(scrapy.Spider):
    name = 'ohiopdf'
    allowed_domains = ['www.ohiohouse.gov']
    start_urls = ['http://www.ohiohouse.gov/committee/standing-committees']

    def parse(self, response):
        #Code below is automatic scraping (for all committees). Takes once long time and not error free.
        for x in response.xpath('//h3/a[@class="black"]').extract():
            folder = Selector(text=x).xpath('//a/text()').extract_first() # folder = committee
            os.makedirs('./ohio/' + folder, exist_ok=True)
            yield Request(response.urljoin(Selector(text=x).xpath('//a/@href').extract_first()), 
                          callback=self.parsedate, 
                          meta={'fol': folder })

    def parsedate(self, response):
        i = -1
        for x in response.xpath('//div[@class="collapsibleListHeader"]/h3/text()').extract():
            folder = './ohio/' + response.meta.get('fol') + '/' + x
            os.makedirs(folder, exist_ok=True)
            i += 1
            yield Request(response.url, 
                          callback=self.parsebill, 
                          meta={'table': response.xpath('//div[@class="collapsibleList"]').extract()[i], 
                                'fol': folder, 
                                'date': x}, 
                          dont_filter=True)

    def parsebill(self, response):
        # tbl - bill pdf files
        tbl = Selector(text=response.meta.get('table')).response.xpath('//td/a[not(contains(text(), "Download")) and (contains(@href, ".pdf") or not(contains(@href, ".pdf"))  ) and not(contains(@href, "../")) and not(contains(@href, ".ics") ) ]').extract()
        # td[3] - org td[4] - stance
        tbl1 = Selector(text=response.meta.get('table')).xpath('//table/tr/th[contains(text(), "Organization")]/ancestor::table/tr/td[3]/text()').extract()
        tbl2 = Selector(text=response.meta.get('table')).xpath('//table/tr/th[contains(text(), "Organization")]/ancestor::table/tr/td[4]/text()').extract()
        tbl3 = Selector(text=response.meta.get('table')).xpath('//table/tr/th[contains(text(), "Organization")]/ancestor::table/tr/td[2]/preceding::table/tr/th[contains(text(), "Bill")]/ancestor::table/tr/td[1]/a/text()').extract()
        
        tbl1 = ['none'] if not tbl1 else tbl1
        tbl2 = ['none'] if not tbl2 else tbl2
        tbl3 = ['none'] if not tbl3 else tbl3 # all bills together

        zlist = list(zip(tbl1, tbl2))
        for org, stance in zlist:
            # yield OhiopdfItem(organization=org, stance=stance, bill=', '.join(tbl3), date=response.meta.get('date'))
            links = []

            for x in tbl:
                link = Selector(text=x).xpath('//a/@href').extract_first() # bill link
                link = link if link is not None and link != '' else response.url # else: do the self link
                links.append(link)
                
            yield OhiopdfItem(organization=org, stance=stance, 
                              bill_name=', '.join(tbl3), date=response.meta.get('date'),
                              state='ohio', session='2017',
                              chamber='House', topic='#TODO',
                              md5='#TODO', html='#TODO',
                              url='\n'.join(links), text='#TODO')

    #     for x in tbl:
    #         folder = response.meta.get('fol') + '/' + Selector(text=x).xpath('//a/text()').extract_first() # bill name (folder)
    #         os.makedirs(folder, exist_ok=True)
            
    #         link = Selector(text=x).xpath('//a/@href').extract_first() # bill link
    #         link = link if link is not None and link != '' else response.url # else: do the self link
    #         yield Request(link, 
    #                       callback=self.parsesave, 
    #                       meta={'descr': response.meta.get('table'), 'fol': folder }, 
    #                       dont_filter=True)

    # def parsesave(self, response):
    #     filename = response.url.split('/')[-1] if response.url.split('/')[-1].split('.')[-1] == 'pdf' else 'There is no PDF file on the site'

    #     with open(response.meta.get('fol') + '/' + 'Organization, Stance, etc.htm', 'wb') as f:
    #         f.write(response.meta.get('descr').encode())

    #     with open(response.meta.get('fol') + '/' + filename, 'wb') as f:
    #         f.write(response.body)

