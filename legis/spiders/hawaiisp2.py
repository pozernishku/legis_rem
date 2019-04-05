# -*- coding: utf-8 -*-
import hashlib
import scrapy
import os
from bs4 import BeautifulSoup
import io
from PIL import Image
import pytesseract
from wand.image import Image as wi
from legis.read_data import convert_pdf_to_txt
from legis.items import HawaiiItem2


class Hawaiisp2Spider(scrapy.Spider):
    name = 'hawaiisp2'
    allowed_domains = ['www.capitol.hawaii.gov']
    start_urls = ['http://www.capitol.hawaii.gov/']
    start_urls = ['http://www.capitol.hawaii.gov/session{}/bills/'.format(year) for year in range(2007, 2008)]

    def parse(self, response):
        session = response.url.split('/')[-3][7:]
        docs = list(zip(response.xpath('//body/pre/a[contains(@href, "bills")]/@href').extract(), response.xpath('//body/pre/text()').extract()))
        for doc, date in docs:
            if doc[-4:].lower() == '.htm': # go only through htm docs
                yield response.follow(doc, self.parse_save, meta={'session': session, 'date': date[:19].strip(), 'download_timeout': 3500})

    def parse_save(self, response):
        folder = './hawaii/{}/'.format(response.meta.get('session'))
        filename = response.url.split('/')[-1]

        os.makedirs(folder, exist_ok=True)
        with open(folder + filename, 'wb') as f:
            f.write(response.body)

        text = ''
        # if filename[-4:].lower() == '.htm':
        soup = BeautifulSoup(response.text, 'html5lib')
        for script in soup(["script", "style"]):
            script.extract() # remove script and style tags
        text = soup.get_text()

        session = response.meta.get('session')
        date = response.meta.get('date')
        md5 = hashlib.md5(response.body).hexdigest()
        if 'Only the PDF version of this document is available at this time' not in text:
            yield HawaiiItem2(url=response.url,
                            state='hawaii',
                            text=text,
                            session=session,
                            date=date,
                            md5=md5)