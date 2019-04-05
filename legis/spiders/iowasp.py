# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl iowasp -t csv -o - > iowasp.csv
"""
import hashlib
import os
from urllib.parse import parse_qs, urlparse
from itertools import product
from bs4 import BeautifulSoup
import scrapy
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from legis.items import IowaspItem


class IowaspSpider(scrapy.Spider):
    name = 'iowasp'
    allowed_domains = ['www.legis.iowa.gov', 'coolice.legis.iowa.gov']
    start_urls = ['http://www.legis.iowa.gov/legislation/billTracking/billDisposition']

    def parse(self, response):
        sessions = response.xpath('//li[@class="select nocsscolor"]').extract()
        for session in sessions:
            sess_id = Selector(text=session).xpath('//li[@class="select nocsscolor"]/@data-ga').extract_first()
            sess_name = Selector(text=session).xpath('//li[@class="select nocsscolor"]/a/text()').extract_first() + \
                        Selector(text=session).xpath('//li[@class="select nocsscolor"]/a/span/text()').extract_first()
            
            l = product(['https://www.legis.iowa.gov/legislation/billTracking/billDisposition?v.template=legislation/billDispositionAjax&layout=false&ga={}&layout=false&chamberID='.format(sess_id)], ['H', 'S'])
            
            for link in l:
                yield response.follow(''.join(link), callback=self.parse_bill, meta={'session': sess_name, 'chamber': link[1], 'sess_id': sess_id} )

    def parse_bill(self, response):
        # links = LinkExtractor(allow=r'BillBook').extract_links(response)
        rows = response.xpath('//tr').extract()[1:]
        for row in rows:
            yield response.follow(Selector(text=row).xpath('//a/@href').extract_first(), 
                                    callback=self.parse_content, meta={'session': response.meta.get('session'),
                                                                      'chamber': response.meta.get('chamber'),
                                                                      'bill': Selector(text=row).xpath('//a/text()').extract_first(),
                                                                      'sess_id': response.meta.get('sess_id'),
                                                                      'date': Selector(text=row).xpath('//td[3]/text()').extract_first() } )

        # for link in links:
        #     yield response.follow(link.url, callback=self.parse_content, meta={'session': response.meta.get('session'), 
        #                                                                        'chamber': response.meta.get('chamber'), 
        #                                                                        'bill': link.text,
        #                                                                        'sess_id': response.meta.get('sess_id')})

    def parse_content(self, response):
        o = urlparse(response.url)
        bill = parse_qs(o.query).get('ba')[0]
        meta = response.meta
        meta['sess_id'] = response.meta.get('sess_id')
        link = 'http://coolice.legis.iowa.gov/Cool-ICE/default.asp?Category=Lobbyist&Service=DspReport&ga={0}&type=b&hbill={1}'.format(response.meta.get('sess_id'), bill)
        yield response.follow(link, callback=self.parse_save, meta=meta)
        
    def parse_save(self, response):
        chamber = 'House' if response.meta.get('chamber') == 'H' else 'Senate'
        sess_id = response.meta.get('sess_id')
        session = response.meta.get('session')
        bill = response.meta.get('bill')
        url = response.url
        date = response.meta.get('date')

        filename = sess_id+'-'+bill+'-'+chamber+'-Lobbyist Declarations.htm'
        os.makedirs('./iowa/', exist_ok=True)
        with open('./iowa/' + filename, 'wb') as f:
            f.write(response.body)
        # yield IowaspItem(session=session, chamber=chamber, bill=bill, url=url, filename=filename)

        soup = BeautifulSoup(response.text, 'html5lib')
        for script in soup(["script", "style"]):
            script.extract() # remove script and style tags
        text = soup.get_text()

        md5 = hashlib.md5(response.text.encode('utf-8')).hexdigest()

        topic = '#TODO'

        yield IowaspItem(session=session, chamber=chamber, 
                        bill_name=bill, url=url, state='iowa', 
                        html=response.text, text=text, 
                        md5=md5, date=date, topic=topic)
