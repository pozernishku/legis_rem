# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl flopdf -t csv -o - > flopdf.csv
- To grab the data with OCR conversion: 
scrapy crawl flopdf -s LOG_FILE=scrapy82.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=2 -t csv -o - > flopdf82.csv
"""
import hashlib
import re
import os
import io
import scrapy
from scrapy.http.request import Request
from PIL import Image
import pytesseract
from wand.image import Image as wi
from legis.items import FlopdfItem
from legis.read_data import convert_pdf_to_txt


class FlopdfSpider(scrapy.Spider):
    name = 'flopdf'
    allowed_domains = ['www.myfloridahouse.gov']
        
    start_urls = [ # to extract term ids
        'http://www.myfloridahouse.gov/Sections/Committees/committees.aspx?LegislativeTermId=82'
    ]

    def parse(self, response):
        termids = response.xpath('//div[@class="c_SessionSelection"]/select/option/@value').extract()
        #termids = ['82'] # comment line above and uncomment this line to grab the data session by session (2004-2006, 2002-2004, etc)
        for termid in termids:
            yield response.follow('http://www.myfloridahouse.gov/Sections/Committees/committees.aspx?LegislativeTermId={}'.format(termid), callback=self.parse_main)

    def parse_main(self, response):
        folder = response.xpath('//div[@class="c_SessionSelection"]/select/option[@selected="selected"]/text()').extract_first().strip() # first year period 
        os.makedirs('./florida/' + folder, exist_ok=True) # 2006 - 2008 (test)
        
        hrefs = response.xpath('//a[contains(@href, "CommitteeId=")]/@href').extract()
        for href in hrefs:
            yield Request(response.urljoin(href), callback=self.parsecomm, meta={'fol': folder})

    def parsecomm(self, response):
        committeename = response.xpath('//h1[@class="cd_ribbon"]/text()').extract_first().split('Speaker')
        committeename = committeename[0][:-14] if len(committeename) > 1 else committeename[0]
        # folder = os.path.join(os.getcwd(), committeename)
        folder = './florida/{0}/{1}/'.format(response.meta.get('fol'), committeename)
        os.makedirs(folder, exist_ok=True)
        committeeid = response.url.split('=')[-1]
        sessions = list(zip(response.xpath('//select[@class="cd_input"]/option/text()').extract(), response.xpath('//select[@class="cd_input"]/option/@value').extract()))
        for session in sessions:
            url = 'http://www.myfloridahouse.gov/Sections/Documents/publications.aspx?CommitteeId={0}&PublicationType=Committees&DocumentType=All&SessionId={1}'.format(committeeid, session[1])
            yield Request(url, callback=self.parsenext, meta={'folder': folder, 'folsession': session[0], 'com': committeename })

    def parsenext(self, response):
        # folder = os.path.join(os.getcwd(), response.meta.get('com'), response.meta.get('folsession') )
        folder = os.path.join(response.meta.get('folder'), response.meta.get('folsession'))
        os.makedirs(folder, exist_ok=True)

        files = list(zip(list(map(str.strip, response.xpath('//a[contains(@href, "DocumentType=Action Packets")]/text()').extract())), list(map(response.urljoin, response.xpath('//a[contains(@href, "DocumentType=Action Packets")]/@href').extract())) ))
        for file in files:
            yield Request(file[1], callback=self.parsesave, meta={'filename': file[0] + '.pdf', 'fol': folder, 'url': response.url, 'download_timeout': 3500})
            
    def parsesave(self, response):
        # with open(os.path.join(response.meta.get('fol'), response.meta.get('filename') ), 'wb') as f:
        #     f.write(response.body)

        # text = '[InternetShortcut]\nURL={}'.format(response.meta.get('url'))

        # with open(os.path.join(response.meta.get('fol'), 'All Committee Publications.url'), 'wb') as u:
        #     u.write(text.encode())

        # yield FlopdfItem(url=response.url, url_all=response.meta.get('url'), filename=response.meta.get('filename'), folder=response.meta.get('fol'))

        state = 'florida'

        session = response.meta.get('fol')
        session = session.split('/')[2][:11].strip().replace(' ', '') if session else ''

        md5 = hashlib.md5(response.body).hexdigest()

        date = response.url.split('=')[-1].replace('%20','')
        regex = r'[0-9]{1,2}-[0-9]{1,2}-[0-9]{1,4}'
        date = re.findall(regex, date) if date else ''
        date = date[0].replace('-', '/') if date else ''

        html = ''

        # text from pdf
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        pdf_text = convert_pdf_to_txt(bfr) if response.url.strip()[-4:].lower() == '.pdf' else 'unsupported file'

        # recognized text (OCR) from pdf
        if len(pdf_text.strip()) <= 50:
            with wi(filename=response.url, resolution=170) as pdf:
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

        topic = '#TODO'

        regex = r'(?:[HSC]{1,1}[BMSPCRJ]{1,1}[RB]{0,1}/)*[HSC]{1,1}[BMSPCRJ]{1,1}[RB]{0,1}[ ]{1,3}[0-9]{2,4}'
        bill_name = ', '.join(list(set(re.findall(regex, pdf_text))))

        chamber = 'House'
        
        yield FlopdfItem(url=response.url, state=state,
                         session=session, md5=md5,
                         date=date, text=pdf_text,
                         html=html, topic=topic,
                         chamber=chamber, bill_name=bill_name)
