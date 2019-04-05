# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl hawaiisp -t csv -o - > hawaii.csv
If you want to scrape pdf files also, uncomment three lines of code in parse() function
There are also commented lines for saving htm files
"""
import hashlib
import os
from bs4 import BeautifulSoup
import scrapy
from legis.items import HawaiiItem


class HawaiispSpider(scrapy.Spider):
    name = 'hawaiisp'
    allowed_domains = ['www.capitol.hawaii.gov']
    start_urls = ['http://www.capitol.hawaii.gov/session{}/commreports/'.format(year) for year in range(1999, 2018)]

    def parse(self, response):
        year = response.url.split('/')[-3][7:]
        htms = response.xpath('//a[contains(translate(text(), ".HTM", ".htm"), ".htm" )]/@href').extract()
        for htm in htms:
            yield response.follow(htm, self.parse_save, meta={'year': year, 'htm_list': response.text})
        # pdfs = response.xpath('//a[contains(translate(text(), ".PDF", ".pdf"), ".pdf" )]/@href').extract()
        # for pdf in pdfs:
        #     yield response.follow(pdf, self.parse_save, meta={'year': year})

    def parse_save(self, response):
        folder = './hawaii/{}/'.format(response.meta.get('year'))
        filename = response.url.split('/')[-1]

        # os.makedirs(folder, exist_ok=True)
        # with open(folder + filename, 'wb') as f:
        #     f.write(response.body)

        soup = BeautifulSoup(response.text, 'html5lib')
        for script in soup(["script", "style"]):
            script.extract() # remove script and style tags
        text = soup.get_text()

        bill_list = response.xpath('//p[contains(text(), "RE:")]/self::* | //p[contains(text(), "RE:")]/following-sibling::p[position() <=3]').extract()
        bill_list = ''.join([b for b in bill_list if 'honorable' not in b.lower() if 'speaker' not in b.lower()])
        soup_bill = BeautifulSoup(bill_list, 'html5lib')
        bill_list = soup_bill.get_text('\n', strip=True).replace('RE:', '').strip()
        bill_list = response.url.split('/')[-1].split('_')[0] if bill_list == '' else bill_list

        session = response.meta.get('year')

        chamber = ''

        date_text = response.meta.get('htm_list')
        ic = date_text.index(response.url.split('/')[-1])
        date_text = date_text[ic-85:ic-35]
        ic = date_text.index(',') + 2
        im = date_text.index(':') + 6
        date_text = date_text[ic:im]

        md5 = hashlib.md5(response.text.encode('utf-8')).hexdigest()

        topic = ''

        yield HawaiiItem(url=response.url, 
                        state='hawaii',
                        html=response.text, 
                        text=text, 
                        bill_name=bill_list,
                        session=session, 
                        chamber=chamber, 
                        date=date_text,
                        md5=md5,
                        topic=topic)

