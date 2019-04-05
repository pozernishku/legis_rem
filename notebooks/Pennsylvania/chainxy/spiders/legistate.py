import scrapy
import json
import csv
from scrapy.spiders import Spider
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem
from lxml import etree
import time
# import geocoder
import pdb

class LegistateSpider(scrapy.Spider):
    name = "legistate"

    start_urls = ["http://www.legis.state.pa.us/CFDOCS/Legis/TR/Public/tr_finder_public.cfm"]
    storeNumbers = []
    base_url = "http://www.legis.state.pa.us/CFDOCS/Legis/TR/Public/tr_finder_public_action.cfm?tr_doc_typ=T&billBody=&billTyp=&billNbr=&hearing_month=&hearing_day=&hearing_year=&NewCommittee=$z$&subcommittee=&subject=&bill=&new_title=&new_salutation=&new_first_name=&new_middle_name=&new_last_name=&new_suffix=&hearing_loc="

    def parse(self, response):
        values = response.xpath('//select[@id="NewCommittee"]//option/@value').extract()

        count = 0
        for val in values:
            if val == '':
                continue
            val = val.replace(' ', '+')

            yield scrapy.Request(url=self.base_url.replace('$z$' ,val), callback=self.parse_list)

    def parse_list(self, response):
        pdf_links = response.xpath('//table[@class="DataTable"]//a/@href').extract()

        for url in pdf_links:
            if 'pdf' in url:
                yield scrapy.Request(url=url, callback=self.parse_pdf)

    def parse_pdf(self, response):
        item = ChainItem()
        item['url'] = response.url
        item['year'] = response.url.split('/')[-1].split('.')[0].split('_')[0]
        item['filename'] = response.url.split('/')[-1]
        with open(item['filename'], "wb") as f:
            f.write(response.body)

        yield item