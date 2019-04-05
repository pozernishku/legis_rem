import scrapy
from oregon.items import OregonItem
import os

from selenium import webdriver
import time
from lxml import html

class OregonSpider(scrapy.Spider):
    name = "oregon"
    domain = "https://olis.leg.state.or.us"
    pdf_dir = "pdf_files"
    history = []

    def __init__(self):
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
        self.driver = webdriver.Chrome("./chromedriver")

    def start_requests(self):
        yield scrapy.Request(url=self.domain + "/liz/2017I1#", callback=self.parse_session_url)

    def parse_session_url(self, response):
        url = "https://olis.leg.state.or.us/liz/%s/Navigation/SessionSelect?_=1504386251516" % response.url.split('/')[4]
        yield scrapy.Request(url=url, callback=self.parse_sessions)

    def parse_sessions(self, response):
        sessions = response.xpath('//ul[@class="no-list-style"]//a')
        bill_urls = []
        for session in sessions[1:]:
            session_label = self.validate(session.xpath('./text()'))
            self.driver.get(self.domain + self.validate(session.xpath('./@href')))
            self.driver.find_element_by_xpath("//li[@id='navigation-2']//a").click()
            time.sleep(10)
            self.driver.find_element_by_xpath("//a[@href='#senateBills']").click()
            self.driver.find_element_by_xpath("//a[@href='#houseBills']").click()
            time.sleep(10)

            tree = html.fromstring(self.driver.page_source.encode("utf8"))
            temp = tree.xpath('//ul[@id="billsTop"]//a/@href')
            for tp in temp:
                if "#" not in tp:
                    bill_urls.append([session_label, self.domain + tp.replace("Overview", "Exhibits")])
            break

        self.driver.close()
        for url in bill_urls:
            request = scrapy.Request(url=url[1], callback=self.parse_doc)
            request.meta['session'] = url[0]
            yield request

    def parse_doc(self, response):
        docs = response.xpath("//div[@id='exhibits']//table//tbody//tr")
        for doc in docs:
            url = self.validate(doc.xpath(".//a/@href"))
            request = scrapy.Request(url=self.domain + url, callback=self.save_pdf)
            request.meta['session'] = response.meta['session']
            request.meta['bill'] = response.url.split('/')[-1]
            request.meta['date'] = self.validate(doc.xpath(".//td[5]//a/text()"))
            request.meta['committee'] = self.validate(doc.xpath(".//td[6]//a/text()"))
            # yield request

            item = OregonItem()
            item['bill'] = request.meta['bill']
            item['session'] = " ".join([tp.strip() for tp in response.meta['session'].split(' ') if tp.strip() != ''])
            item['committee'] = request.meta['committee']
            item['date'] = request.meta['date']
            item['url'] = url
            item['filename'] = url.split('/')[4] + "_" + url.split("/")[-1] + ".pdf"
            yield item

    def save_pdf(self, response):
        item = OregonItem()
        with open("%s/%s.pdf" % (self.pdf_dir, response.url.split('/')[4] + "_" + response.url.split("/")[-1]), "wb") as fp:
            fp.write(response.body)
        item['bill'] = response.meta['bill']
        item['session'] = " ".join([tp.strip() for tp in response.meta['session'].split(' ') if tp.strip() != ''])
        item['committee'] = response.meta['committee']
        item['date'] = response.meta['date']
        item['url'] = response.url
        item['filename'] = response.url.split('/')[4] + "_" + response.url.split("/")[-1] + ".pdf"
        
        if item['url'] not in self.history:
            self.history.append(item['url'])
            yield item

    def validate(self, xpath_obj):
        try:
            return xpath_obj.extract_first().strip()
        except:
            return ""
