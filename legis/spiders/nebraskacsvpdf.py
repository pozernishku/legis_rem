# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl nebraskacsvpdf -t csv -o - > nebraskacsv.csv
"""
import os
import scrapy
from legis.items import NebraskaItem


class NebraskacsvpdfSpider(scrapy.Spider):
    name = 'nebraskacsvpdf'
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'FEED_EXPORT_FIELDS': ["title", "filename"]
    }
    allowed_domains = ['www.nebraskalegislature.gov']
    start_urls = ['http://www.nebraskalegislature.gov/transcripts/search_past.php']

    def parse(self, response):
        legids = response.xpath('//div/label[@class="btn btn-sm btn-default btn-checkbox other-leg"]/input/@value').extract()
        for legid in legids:
            link = 'http://www.nebraskalegislature.gov/transcripts/search_transcripts.php?start=0&keyword=committee&fuzzy=Y&legs[]={0}&type[]=Committee'.format(legid)
            yield response.follow(link, self.parsenext, meta={'legid': legid}, dont_filter=True )
        
    def parsenext(self, response):
        count = response.xpath('//div[@class="col-sm-6 text-right hidden-xs"]/p/strong[3]/text()').extract_first()
        count = int(count) if count is not None else -1
        legid = response.meta.get('legid')

        if count > -1:
            for start in range(0, count, 25):
                if start < count:
                    link = 'http://www.nebraskalegislature.gov/transcripts/search_transcripts.php?start={1}&keyword=committee&fuzzy=Y&legs[]={0}&type[]=Committee'.format(legid, start)
                    yield response.follow(link, self.parselist, dont_filter=True)

    def parselist(self, response):
        titles = response.xpath('//div[@class="main-content"]/div/div/h2/text()').extract()
        links = response.xpath('//div[@class="main-content"]/div/div[@class="panel-body"]/ul/li[1]/a/@href').extract()
        
        filenames = list(zip(titles, links))

        for title, link in filenames:
            yield response.follow(link, self.parsesave, meta={'title': title, 'download_timeout': 3500}, dont_filter=True )

    def parsesave(self, response):
        os.makedirs('./nebraska/', exist_ok=True)
        title = response.meta.get('title')
        filename = response.url

        with open('./nebraska/' + title.replace('/', '-') + '.pdf', 'wb') as f:
            f.write(response.body)

        yield NebraskaItem(title = title, filename = filename)
        