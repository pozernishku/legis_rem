# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl mainesp -t csv -o - > mainesp.csv

These parameters are changed to appropriate years values:
hStatYYFr, hStatYYTo, sStatYYFr, sStatYYTo
"""
import hashlib
import calendar
import datetime
import json
import os
import io
from scrapy.http import FormRequest
import scrapy
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from wand.image import Image as wi
from legis.items import MaineItem
from legis.read_data import convert_pdf_to_txt


class MainespSpider(scrapy.Spider):
    name = 'mainesp'
    allowed_domains = ['legislature.maine.gov']

    def start_requests(self): # year until 2030
        # return [FormRequest('https://legislature.maine.gov/legis/bills/search_ps.asp',
        #                     formdata={'PID': '0', 'snum': '0', 'paperNumberPrefix': '%', 'sec1': '0', 'amend_filing_no_prefix': '%', 'sec2': '0', 
        #                     'sec3': '0', 'phYYFr': '2017', 'phYYTo': '2017', 'wkYYFr': '2017', 'wkYYTo': '2017', 'sec4': '0', 'sponsorSession': '0',
        #                     'sec5': '1', 'hStatMMFr': '1', 'hStatDDFr': '1', 'hStatYYFr': str(y), 'hStatMMTo': '12', 'hStatDDTo': '31', 'hStatYYTo': str(y), 
        #                     'sStatMMFr': '1', 'sStatDDFr': '1', 'sStatYYFr': str(y), 'sStatMMTo': '12', 'sStatDDTo': '31', 'sStatYYTo': str(y), 'sec6': '0', 
        #                     'sec7': '0', 'sec10': '0', 'tmyYYFr': '2017', 'tmyYYTo': '2017', 'submit': 'Search'}  )
        #                     for y in range(2012, 2031)
        #                      ]


        return [FormRequest('https://legislature.maine.gov/legis/bills/search_ps.asp',
                            formdata={'PID': '0', 'snum': '0', 'paperNumberPrefix': '%', 'sec1': '0', 'amend_filing_no_prefix': '%', 'sec2': '0', 
                            'sec3': '0', 'phYYFr': '2018', 'phYYTo': '2018', 'wkYYFr': '2018', 'wkYYTo': '2018', 'sec4': '0', 'sponsorSession': '0',
                            'sec5': '1', 'hStatMMFr': '1', 'hStatDDFr': '1', 'hStatYYFr': str(y), 'hStatMMTo': '12', 'hStatDDTo': '31', 'hStatYYTo': str(y), 
                            'sStatMMFr': '1', 'sStatDDFr': '1', 'sStatYYFr': str(y), 'sStatMMTo': '12', 'sStatDDTo': '31', 'sStatYYTo': str(y), 'sec6': '0', 
                            'sec7': '0', 'sec10': '0', 'tmyYYFr': '2018', 'tmyYYTo': '2018', 'submit': 'Search'}  )
                            for y in range(2018, 2019)
                             ]

    def parse(self, response):
        links = response.xpath('//a[@class="small_wide_info_btn" and contains(text(), "Committee Testimony") ]/@href').extract()
        headers = response.xpath('//a[@class="small_wide_info_btn" and contains(text(), "Committee Testimony") ]/ancestor::span/ancestor::td/ancestor::tr/preceding-sibling::tr[1]/td[contains(@class, "RecordNumbers")]').extract()
        elements = list(zip(links, headers))
        for link, header in elements:
            yield response.follow(link, callback=self.parse_testimony, meta={'header': header}, dont_filter=True)

    def parse_testimony(self, response):
        script = response.xpath('//script/text()').extract()[-1]
        script_lines = script.splitlines()
        snum = [line for line in script_lines if 'var session_number' in line][0].split('=')[-1].strip(' ";')
        paper = [line for line in script_lines if 'var paper_number_string' in line][0].split('=')[-1].strip(' ";')
        recid = [line for line in script_lines if 'var recID' in line][0].split('=')[-1].strip(' ";')
        link = 'https://legislature.maine.gov/legis/bills/getPHWS.asp?snum={0}&paper={1}'.format(snum, paper)
        yield response.follow(link, callback=self.parsedate, meta={'header': response.meta.get('header'), 'recid': recid }, dont_filter=True )

    def parsedate(self, response):
        hearingDate = json.loads(response.text)
        if hearingDate:
            hearingDate, date = hearingDate[0]['hearingDate'].split(), hearingDate[0]['hearingDate']
            months = dict((v,k) for k,v in enumerate(calendar.month_abbr))
            dt = datetime.datetime(int(hearingDate[-1]), months.get(hearingDate[1]), int(hearingDate[2]) )
            epoch = datetime.datetime.fromtimestamp(0)
            dst = hearingDate[-2]
            appendID = int((dt - epoch).total_seconds())
            appendID = appendID if dst == 'EDT' else appendID + 3600
            
            link = 'https://legislature.maine.gov/legis/bills/getTestyRecords.asp?recid={0}&date={1}'.format(response.meta.get('recid'), appendID )
            yield response.follow(link, self.parselist, meta={'header': response.meta.get('header'), 'date': date}, dont_filter=True )
        
    def parselist(self, response):
        pdflines = json.loads(response.text)
        soup = BeautifulSoup(response.meta.get('header'), 'html5lib')
        bill = soup.get_text()
        for pdfline in pdflines:
            pdfid = str(pdfline.get('id'))
            filename = str(pdfline.get('lastName')) + ', ' + str(pdfline.get('firstName')) + ' - ' + pdfid + '.pdf'
            name = pdfline.get('organization')
            yield response.follow('https://legislature.maine.gov/legis/bills/getTestimonyDoc.asp?id={0}'.format(pdfid), 
                                  callback=self.parsesave,
                                  meta={'bill': bill, 'filename': filename, 'name': name, 'date': response.meta.get('date'),
                                        'download_timeout': 3500 }, dont_filter=True )

    def parsesave(self, response):
        filename = response.meta.get('filename')
        os.makedirs('./maine/', exist_ok=True)
        with open('./maine/' + filename.replace('/', '-'), 'wb') as f:
            f.write(response.body)

        # yield MaineItem(bill=response.meta.get('bill'), filename=filename.replace('/', '-'), name=response.meta.get('name'), url=response.url )
        bill = response.meta.get('bill')

        session = bill.split(' ')[-2]

        state = 'maine'

        bill_name = bill.split(session)[0].strip(', ')

        md5 = hashlib.md5(response.body).hexdigest()

        html = ''

        url = response.url

        date = response.meta.get('date')

        chamber = {'CO': 'Senate', 'HC': 'House', 'HO': 'House', 'HP': 'House', 'HS': 'House', 
                   'IB': 'House', 'SA': '', 'SC': 'Senate', 
                   'SO': 'Senate', 'SP': 'House & Senate', 'SR': 'Senate', 'SS': 'Senate'}

        for i in chamber:
            if i in bill_name:
                chamber = chamber.get(i)
                break

        topic = '#TODO'

        # text from pdf
        # bytesio = io.BytesIO(response.body)
        # bfr = io.BufferedReader(bytesio)
        # pdf_text = convert_pdf_to_txt(bfr) if response.url.strip()[-4:].lower() == '.pdf' else 'unsupported file'

        # # recognized text (OCR) from pdf
        # if len(pdf_text.strip()) <= 50:
        #     with wi(filename=response.url, resolution=200) as pdf:
        #         pdfImage = pdf.convert('jpeg')
        #         imageBlobs = []
        #         for img in pdfImage.sequence:
        #             with wi(image = img) as imgPage:
        #                 imageBlobs.append(imgPage.make_blob('jpeg'))
                        
        #     recognized_text = []

        #     for imgBlob in imageBlobs:
        #         im = Image.open(io.BytesIO(imgBlob))
        #         text = pytesseract.image_to_string(im, lang = 'eng')
        #         recognized_text.append(text)

        #     recognized_text = '\n\n\n'.join(recognized_text)

        # pdf_text = pdf_text if len(pdf_text.strip()) > 50 else recognized_text

        yield MaineItem(md5=md5, html=html,
                        session=session, bill_name=bill_name,
                        url=url, state=state,
                        date=date, chamber=chamber,
                        topic=topic, text='' #pdf_text
                        )
