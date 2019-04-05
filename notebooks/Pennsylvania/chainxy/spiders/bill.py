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

class BillSpider(scrapy.Spider):
    name = "bill"

    start_urls = ["https://le.utah.gov/Documents/bills.htm"]
    storeNumbers = []
    base_url = "https://le.utah.gov"

    def parse(self, response):
        urls = response.xpath('//blockquote/p[2]/a/@href').extract()

        count = 0
        for url in urls:
            yield scrapy.Request(url=self.base_url + url, callback=self.parse_list)

    def parse_list(self, response):
        bill_code_links = response.xpath('//div[@id="g1"]/ul//a/@href').extract()

        header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, sdch, br',
            'Accept-Language':'en-US,en;q=0.8',
            'Connection':'keep-alive',
            'Cookie':'JSESSIONID=2AD4D310F4CAF4240A9EBD54E5E204BA; ASPSESSIONIDCAUTBTRC=NONKMNKCNKEOPPHKHBOJCALF; ASPSESSIONIDCAQXBTRC=MHCPMNKCGGOAKAIJAHGEGEAM; utreadcalHideHSCol=',
            'Host':'le.utah.gov',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        if len(bill_code_links) != 0:
            year_id = response.url.split('=')[1]
            for code in bill_code_links:
                code = code[code.find("'r")+2:-1].replace("'", '')
                yield scrapy.Request(url=response.url+'&bills='+code, callback=self.parse_dynalist, headers=header)

    def parse_dynalist(self, response):
        links = response.xpath('//a/@href').extract()
        header = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Cookie':'JSESSIONID=2AD4D310F4CAF4240A9EBD54E5E204BA; ASPSESSIONIDCAUTBTRC=NONKMNKCNKEOPPHKHBOJCALF; ASPSESSIONIDCAQXBTRC=MHCPMNKCGGOAKAIJAHGEGEAM; utreadcalHideHSCol='
        }

        if len(links) == 0:
            links = etree.HTML(response.xpath('//DATA/text()').extract_first()).xpath('//a/@href')
            # pdb.set_trace()

        for link in links:
            try:
                if 'htm' not in link:
                    continue
                url = self.base_url+link
                # url = url.replace('static', 'hbillenr').replace('html', 'htm').replace('htmdoc/sbillhtm', 'bills/sbillenr').replace('htmdoc/hbillhtm', 'bills/hbillenr')
                yield scrapy.Request(url=url, callback=self.parse_hearing,  headers=header)
            except:
                continue

    def parse_hearing(self, response):
        links = response.xpath('//div[@id="billVideo"]/ul[@class="billinfoulm"]//a/@href').extract()

        for link in links:
            if 'asp' not in link:
                continue
            yield scrapy.Request(url=self.base_url+link, callback=self.parse_table)

    def parse_table(self, response):
        links = response.xpath('//table[@class="UItable"]//a/@href').extract()

        for link in links:
            if 'Minute' in link:
                url = link.split("'")[1]
                if 'htm' in url:
                    yield scrapy.Request(url=self.base_url+url, callback=self.parse_bill)                    
                continue
            if 'minutes' in link:
                url = link.split("'")[1]
                if 'htm' in url:
                    yield scrapy.Request(url=self.base_url+url, callback=self.parse_bill_1)

    def parse_bill(self, response):
        item = ChainItem()
        item['url'] = response.url
        item['year'] = response.url.split('/')[5]
        item['bill'] = response.url.split('/')[-1].split('.')[0]
        item['content'] = response.xpath('//body').extract()
        yield item

    def parse_bill_1(self, response):
        item = ChainItem()
        item['url'] = response.url
        item['year'] = response.url.split("/")[3].replace("~", "")
        item['bill'] = response.url.split('/')[-1].split('.')[0]
        item['content'] = response.xpath('//div[@id="content"]').extract()
        if len(item['content']) == 0:
            item['content'] = response.xpath('//body').extract()

        yield item