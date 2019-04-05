# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl montana -t csv -o - > montana.csv

There are predictable URLs to list of committee meeting minutes 2007-present.
Present year is set manualy here: range(2007, 2018, 2)
For example: http://leg.mt.gov/bills/2015/minutes/Senate/

The minutes are in PDF format, with witnesses and positions under headers
like "Proponents' Testimony".

For example: http://leg.mt.gov/bills/2015/minutes/Senate/150128BUS_Sm1.pdf
"""
import hashlib
import itertools
import io
import re
import scrapy
from scrapy.http.request import Request

from legis.items import MontanaItem
from legis.read_data import convert_pdf_to_txt


class MontanaSpider(scrapy.Spider):
    name = 'montana'
    allowed_domains = ['leg.mt.gov']

    def start_requests(self):
        for year, chamber in itertools.product(range(2007, 2018, 2), ["House", "Senate"]):
            url = 'http://leg.mt.gov/bills/{}/minutes/{}/'.format(year, chamber)
            yield Request(url, meta={'year': year, 'chamber': chamber})

    def parse(self, response):
        urls = response.xpath('//a[contains(text(), ".pdf")]/@href').extract()
        for url in urls:
            yield response.follow(url, self.parse_next, meta=response.meta)

    def parse_next(self, response):
        session, chamber = response.meta.get('year'), response.meta.get('chamber')

        # folder = './montana/{}_{}/'.format(session, chamber)
        filename = response.url.split('/')[-1]
        # os.makedirs(folder, exist_ok=True)
        # with open(folder + filename, 'wb') as f:
        #     f.write(response.body)
        
        # yield MontanaItem(url=response.url, session=session, chamber=chamber)

        state = 'montana'

        year = '20' + filename[:2]
        month = filename[2:4]
        day = filename[4:6]
        date = month + '/' + day + '/' + year # date comes from the name of the file. Need to format it in 4/20/2015

        md5 = hashlib.md5(response.body).hexdigest()

        html = ''
        
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        pdf_text = convert_pdf_to_txt(bfr)

        indx = pdf_text.find('Date Posted:')
        bill_txt = pdf_text[:indx+300].strip() if indx != -1 else ''
        regex = r'[A-Z]{2,5} [0-9]{2,5}'
        bill_name = ', '.join(re.findall(regex, bill_txt))

        topic = '#TODO'

        yield MontanaItem(url=response.url, session=session, 
                            chamber=chamber, state=state,
                            date=date, md5=md5,
                            html=html, text=pdf_text,
                            bill_name=bill_name, topic=topic)
