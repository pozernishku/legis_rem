# -*- coding: utf-8 -*-
"""
Notes
Run this spider only after running wygetlist.py
This spider will create csv and export pdf files.
Both spiders work with this setting CONCURRENT_REQUESTS = 1 (already set)
In most cases the minutes files will have this URL https://legisweb.state.wy.us/LegbyYear/IntCommDetail.aspx?strType=M  
So there is a need to go to previous page first f.e. https://legisweb.state.wy.us/LegbyYear/InterimComm.aspx?strCommitteeID=01&Year=2015
to see results

How to run spider.
- Go to legis project directory
- Run: scrapy crawl wyst -t csv -o - > wyst.csv
"""
import os
import csv
import scrapy
from scrapy.http.request import Request
from legis.items import WyItem


class WystSpider(scrapy.Spider):
    name = 'wyst'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1
    }
    allowed_domains = ['legisweb.state.wy.us']

    def start_requests(self):
        with open('comms.csv', newline='') as csvfile:
            urls = csv.reader(csvfile, delimiter='>', quotechar='|')
            for url in list(urls)[1:]:
                if url:
                    yield Request(''.join(url).strip('" '), callback=self.parse, meta={'download_timeout': 2000, 'max_retry_times': 30}, dont_filter=True)

    def parse(self, response):
        if 'strType=M' in response.url:
            comm_name = response.xpath('//span[@id="ctl00_cphContent_lblTitle"]/b/i/font/text()').extract_first().strip()
            #pdf_links = response.xpath('//a[contains(@href, "pdf") and not(contains(@href, "studiesCurrent")) ]/@href').extract()
            pdf_links = response.xpath('//a[(contains(@href, "pdf") or (contains(@href, ".htm") and not(contains(@href, "attorneygeneral"  ) ) )  ) and not(contains(@href, "studiesCurrent")) ]/@href').extract()
            pdf_dates = response.xpath('//a[(contains(@href, "pdf") or (contains(@href, ".htm") and not(contains(@href, "attorneygeneral"  ) ) )  ) and not(contains(@href, "studiesCurrent")) ]/text()').extract()
            #pdf_dates = response.xpath('//a[contains(@href, "pdf") and not(contains(@href, "studiesCurrent")) ]/text()').extract()
            pdfs = list(zip(pdf_links, pdf_dates))
            for pdf_link, pdf_date in pdfs:
                yield response.follow(pdf_link.strip(), callback=self.parsesave, meta={'comm_name': comm_name, 'url': response.url, 'date': pdf_date, 'download_timeout': 2000, 'max_retry_times': 30 }, dont_filter=True )
        elif 'minutes' in response.url.lower():
            pass # write here

    def parsesave(self, response):
        filename = response.url.split('/')[-1]
        yield WyItem(url=response.meta.get('url'), committee=response.meta.get('comm_name'), date=response.meta.get('date'), filename=filename)
        os.makedirs('./wyoming/', exist_ok=True)
        with open('./wyoming/' + filename, 'wb') as f:
            f.write(response.body)
