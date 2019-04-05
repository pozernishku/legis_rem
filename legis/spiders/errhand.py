# -*- coding: utf-8 -*-
import hashlib
import re
import calendar
import datetime
import json
import os
import io
from scrapy.http import FormRequest
from scrapy.http.request import Request
import scrapy
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from wand.image import Image as wi
from legis.items import MaineItem
from legis.read_data import convert_pdf_to_txt


class ErrhandSpider(scrapy.Spider):
    name = 'errhand'
    allowed_domains = ['legislature.maine.gov']
    # start_urls = ['http://legislature.maine.gov/']

    def start_requests(self):
        with open('/Users/zackushka/Downloads/scrapy 2016.log') as f:
            text = f.read()
            regex = r'(?<=ERROR: Spider error processing <GET ).*>'
            text = re.findall(regex, text)
            text = list(map(lambda x: x[:-1], text))

            for url in text:
                yield Request(url)

    def parse(self, response):
        filename = response.meta.get('filename')
        # os.makedirs('./maine/', exist_ok=True)
        # with open('./maine/' + filename.replace('/', '-'), 'wb') as f:
            # f.write(response.body)

        # yield MaineItem(bill=response.meta.get('bill'), filename=filename.replace('/', '-'), name=response.meta.get('name'), url=response.url )
        bill = '' #response.meta.get('bill')

        session = '127th'

        state = 'maine'

        bill_name = ''

        md5 = hashlib.md5(response.body).hexdigest()

        html = ''

        url = response.url

        date = ''

        chamber = 'House & Senate'

        # for i in chamber:
        #     if i in bill_name:
        #         chamber = chamber.get(i)
        #         break

        topic = '#TODO'

        # text from pdf
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        pdf_text = convert_pdf_to_txt(bfr) if response.url.strip()[-4:].lower() == '.pdf' else 'unsupported file'

        # recognized text (OCR) from pdf
        if len(pdf_text.strip()) <= 50:
            with wi(filename=response.url, resolution=200) as pdf:
                pdfImage = pdf.convert('jpeg')
                imageBlobs = []
                for img in pdfImage.sequence:
                    with wi(image = img) as imgPage:
                        imageBlobs.append(imgPage.make_blob('jpeg'))
                        
            recognized_text = []

            for imgBlob in imageBlobs:
                im = Image.open(io.BytesIO(imgBlob))
                text = pytesseract.image_to_string(im, lang = 'eng')
                recognized_text.append(text)

            recognized_text = '\n\n\n'.join(recognized_text)

        pdf_text = pdf_text if len(pdf_text.strip()) > 50 else recognized_text

        yield MaineItem(md5=md5, html=html,
                        session=session, bill_name=bill_name,
                        url=url, state=state,
                        date=date, chamber=chamber,
                        topic=topic, text=pdf_text)

