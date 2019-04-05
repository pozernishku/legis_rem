# -*- coding: utf-8 -*-
"""
Notes
Run this spider first. It will create a correct sequence list of links (comms.csv). It's needed only for 
this site because of 500 server error. Run wyst.py spider after this one.
Both spiders work with this setting CONCURRENT_REQUESTS = 1 (already set)
List http://legisweb.state.wy.us/LSOWEB/Interim.aspx 

How to run spider.
- Go to legis project directory
- Run: scrapy crawl wygetlist -t csv -o - > comms.csv
"""
import scrapy
from scrapy.http.request import Request

class WygetlistSpider(scrapy.Spider):
    name = 'wygetlist'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1
    }
    allowed_domains = ['legisweb.state.wy.us']

    def start_requests(self):
        # urls = [
        #     'https://legisweb.state.wy.us/LegbyYear/IntCommList.aspx?Year={}'.format(year)
        #     for year in range(2009, 2031)
        # ] + ['https://legisweb.state.wy.us/LegislatorSummary/IntCommList.aspx']

        # concat two lists after!!!!!!!!!!!!!

        urls = [
            'http://legisweb.state.wy.us/{}/interim/intcomm.htm'.format(year)
            for year in range(2001, 2009)
        ]

        for url in urls:
            yield Request(url, meta={'download_timeout': 2000, 'max_retry_times': 30})

    def parse(self, response):
        if 'intcomm.htm' in response.url:
            links = response.xpath('//a[contains(@href, "/interim/")]/@href|//a[contains(@href, "/schoolfinance/")]/@href').extract()
            for link in links:
                yield response.follow(link, callback=self.parse_mins, meta={'download_timeout': 2000, 'max_retry_times': 30, 'page': 'intcomm.htm'}, dont_filter=True)
        elif 'IntCommList.aspx' in response.url:
            links = response.xpath('//a[contains(@href, "strCommitteeID=")]/@href').extract()
            for link in links:
                yield response.follow(link, callback=self.parse_mins, meta={'download_timeout': 2000, 'max_retry_times': 30, 'page': 'IntCommList.aspx'}, dont_filter=True)

    def parse_mins(self, response):
        yield {'url': response.url }
        if response.meta.get('page') == 'IntCommList.aspx':
            mins_link = response.xpath('//a[@id="ctl00_cphContent_hlMinutes"]/@href').extract_first()
            mins_link = response.urljoin(mins_link) if mins_link is not None else None
            yield {'url': mins_link}
        elif response.meta.get('page') == 'intcomm.htm':
            mins_links = response.xpath('//a[contains(translate(text(), "MINUTES", "minutes"), "minutes")]/@href').extract()
            mins_links = [response.urljoin(l) if l is not None else None for l in mins_links]
            for link in mins_links:
                yield {'url': link}

