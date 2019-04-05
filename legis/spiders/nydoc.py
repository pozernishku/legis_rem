# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl nydoc -t csv -o - > nydoc.csv
"""
import os
from urllib.parse import parse_qs
from urllib.parse import urlparse
from legis.items import NydocItem
import scrapy
from scrapy.selector import Selector
from scrapy.http.request import Request


class NydocSpider(scrapy.Spider):
    name = 'nydoc'
    allowed_domains = ['www.assembly.state.ny.us',
                       'nystateassembly.granicus.com']
    start_urls = [  # 'http://www.assembly.state.ny.us/av/hearings/',
        'http://nystateassembly.granicus.com/ViewPublisher.php?view_id=8']

    def parse(self, response):
        folders = response.xpath('//div[@class="AccordionPanel"]').extract()
        for folder in folders:
            year = Selector(text=folder).xpath('//div[@class="AccordionPanelTab"]/text()').extract_first()
            os.makedirs('./newyork/' + year)

            rows = Selector(text=folder).xpath('//table[@class="listingTable"]/tbody/tr').extract()
            for row in rows:
                name = Selector(text=row).xpath('//td[@headers="Name"]/text()').extract_first()
                name = name.strip() if name is not None else ''
                length = len(name)
                name = name if length < 235 else name[:235]
                date = Selector(text=row).xpath('//td[contains(@headers, "Date")]/text()').extract_first()
                href = Selector(text=row).xpath('//td/a[contains(text(), "Transcript") or contains(text(), "Transcript and Testimony")]/@href').extract_first()
                t_type = Selector(text=row).xpath('//td/a[contains(text(), "Transcript") or contains(text(), "Transcript and Testimony")]/text()').extract_first()
                if href is not None and 'Transcript' in t_type:
                    yield Request(href, callback=self.parsetranscript, meta={'year': year, 'name': name, 'date': date, 'download_timeout': 3500}, dont_filter=True)
                else:
                    continue

    def parsetranscript(self, response): 
        if 'docs.google.com' in response.url:
            o = urlparse(response.url)
            link = parse_qs(o.query).get('url')[0]
            yield Request(link, callback=self.parsesavepdf, meta=response.meta, dont_filter=True)
        else:
            with open(os.path.join('./newyork/', response.meta.get('year'), response.meta.get('name').replace('/','-') + ' - ' + response.meta.get('date') + '.htm' ), 'wb') as f:
                f.write(response.body)
            yield NydocItem(url=response.url, year=response.meta.get('year'), date=response.meta.get('date'), name=response.meta.get('name'))
    
    def parsesavepdf(self, response):
        with open(os.path.join('./newyork/', response.meta.get('year'), response.meta.get('name').replace('/','-') + ' - ' + response.meta.get('date') + '.pdf' ), 'wb') as f:
            f.write(response.body)
        yield NydocItem(url=response.url, year=response.meta.get('year'), date=response.meta.get('date'), name=response.meta.get('name'))
