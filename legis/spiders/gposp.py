# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl gposp -s LOG_FILE=gposp.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -t csv -o - > gposp.csv
"""
import os
import scrapy
from legis.items import GpoItem


class GpospSpider(scrapy.Spider):
    name = 'gposp'
    allowed_domains = ['www.gpo.gov']
    start_urls = ['https://www.gpo.gov/fdsys/browse/collection.action?collectionCode=CHRG']

    def parse(self, response):
        links = response.xpath('//div[@id="browse-drilldown-mask"]/div/a')
        for link in links:
            sess_name = ''.join(link.xpath('text()').extract()).strip()
            href = response.url + '&' + link.xpath('@onclick').extract_first().split('&')[1]
            yield response.follow(href, callback=self.parse_chamber, meta={'sess_name': sess_name, 'base_url': response.url})

    def parse_chamber(self, response):
        links = response.xpath('//div[@class="level2 browse-level"]/a')
        for link in links:
            hearing_name = ''.join(link.xpath('text()').extract()).strip()
            href = response.meta.get('base_url') + '&' + link.xpath('@onclick').extract_first().split('&')[1]
            response.meta['hearing_name'] = hearing_name
            yield response.follow(href, callback=self.parse_comm, meta=response.meta)

    def parse_comm(self, response):
        links = response.xpath('//div[contains(@class, "level3")]/a')
        for link in links:
            comm_name = ''.join(link.xpath('text()').extract()).strip()
            href = response.meta.get('base_url') + '&' + link.xpath('@onclick').extract_first().split('&')[1]
            response.meta['comm_name'] = comm_name
            yield response.follow(href, callback=self.parse_more, meta=response.meta)

    def parse_more(self, response):
        links = response.xpath('//tr/td/a[3]/@href').extract()
        for link in links:
            yield response.follow(link, callback=self.parse_mods, meta=response.meta)

    def parse_mods(self, response):
        txt = response.xpath('//tr/td/a[contains(text(), "Text")]/@href').extract_first()
        mods = response.xpath('//tr/td/a[contains(text(), "MODS")]/@href').extract_first()
        dir_name = response.url.split('&')[2].split('=')[1]
        response.meta['dir_name'] = dir_name
        yield response.follow(txt, callback=self.parse_save, meta=response.meta)
        yield response.follow(mods, callback=self.parse_save, meta=response.meta)

    def parse_save(self, response):
        dir_name = response.meta.get('sess_name')+' - '+response.meta.get('hearing_name')+' - '+response.meta.get('comm_name')+' - '+response.meta.get('dir_name')
        dir_name = dir_name.replace('/', '-')

        filename = response.url.split('/')[-1]

        response.selector.remove_namespaces()
        witnesses = response.xpath('//witness/text()').extract() if filename.split('.')[-1].lower() == 'xml' else ['']
        witnesses = '\n'.join(witnesses)

        os.makedirs('./gpo_docs/'+dir_name+'/', exist_ok=True)

        with open('./gpo_docs/'+dir_name+'/'+filename, 'wb') as f:
            f.write(response.body)

        yield GpoItem(url=response.url, path=dir_name, witnesses=witnesses)
