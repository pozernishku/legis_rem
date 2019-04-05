# -*- coding: utf-8 -*-
"""
How to run spider. 
- Go to legis project directory
- Run: scrapy crawl mncsv -t csv -o - > mncsv.csv
- There are two lines in the end of the spider defining 
  the text placement, inlines or newlines so you can uncomment one.
"""
import hashlib
import json
import os
from bs4 import BeautifulSoup
import scrapy
from scrapy.selector import Selector
from legis.items import MnItem


class MncsvSpider(scrapy.Spider):
    name = 'mncsv'
    allowed_domains = ['www.house.leg.state.mn.us']
    start_urls = ['http://www.house.leg.state.mn.us/comm/commminutes.asp']

    def parse(self, response):
        periods = response.xpath('//a[contains(@href, "ls_year")]').extract()
        for period in periods:
            yield response.follow(Selector(text=period).xpath('//a/@href').extract_first(), 
                                    callback=self.parseperiod, dont_filter=True, 
                                    meta={'session': Selector(text=period).xpath('//a/text()').extract_first() })

    def parseperiod(self, response):
        committees = list(zip(response.xpath('//a[contains(@href, "comm=")]/@href').extract(), response.xpath('//a[contains(@href, "comm=")]/text()').extract() ) )
        for comm_link, comm_name in committees:
            yield response.follow(comm_link, callback=self.parsecommittee, 
                                    meta={'comm_name': comm_name.replace('/', '-'),
                                            'session': response.meta.get('session') }, dont_filter=True )

    def parsecommittee(self, response):
        dates = json.loads(response.xpath('//input[@id="MinuteObjects"]/@value').extract_first())
        for date in dates:
            yield response.follow(response.url.replace('minutelist', 'minutes') + '&id=' + date['MinuteID'], 
                                    callback=self.parsecontent, 
                                    meta={'date': date['Date'], 
                                            'meettitle': date['MeetTitle'], 
                                            'comm_name': response.meta.get('comm_name'), 
                                            'minuteid': date['MinuteID'],
                                            'session': response.meta.get('session') }, dont_filter=True )

    def parsecontent(self, response):
        url = response.url
        date = response.meta.get('date')

        html = response.xpath('//input[@id="MinHolder"]/@value').extract_first()
        
        meettitle = response.meta.get('meettitle')
        comm_name = response.meta.get('comm_name')
        minuteid = response.meta.get('minuteid')

        #Save files
        # os.makedirs('./minnesota/', exist_ok=True)
        # with open('./minnesota/' + date.replace('/', '-')+'-'+meettitle.replace('/', '-')+'-'+comm_name+'-'+minuteid+'.htm', 'wb') as f:
        #     f.write(text.encode())

        soup = BeautifulSoup(html, 'html5lib') if html is not None else BeautifulSoup('Minutes not found.', 'html5lib') 
        
        # Inlines or newlines
        text = soup.get_text() #inlines
        # text = soup.get_text('\n') #newlines

        state = 'minnesota'

        session = response.meta.get('session')

        md5 = hashlib.md5(html.encode('utf-8')).hexdigest() if html is not None else 'Minutes not found.'

        chamber = 'House' # House only

        topic = '#TODO'

        bill_name = '#TODO'

        # yield MnItem(url = url, date = date, text = text)
        yield MnItem(url=url, date=date, 
                        text=text, state=state,
                        html=html, session=session, 
                        md5=md5, chamber=chamber,
                        topic=topic, bill_name=bill_name)
