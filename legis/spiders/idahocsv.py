# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl idahocsv -s LOG_FILE=scrapy_idahocsv.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=3 -t csv -o - > idahocsv.csv
- You can uncomment the line: <for year in years:> to do all the work for all years.
"""
import hashlib
import io
import os
import scrapy
from scrapy.http import FormRequest
from scrapy.http.request import Request
from legis.items import IdahoItem
from legis.read_data import convert_pdf_to_txt
from PIL import Image
import pytesseract
from wand.image import Image as wi


class IdahocsvSpider(scrapy.Spider):
    name = 'idahocsv'
    allowed_domains = ['lso.legislature.idaho.gov']

    def start_requests(self):
        return [FormRequest('http://lso.legislature.idaho.gov/MediaArchive/ShowMediaByCommittee.do',
                            formdata={
                                'year': '2017', 'category': 'House Standing Committees', 'committeeId': ''},
                            callback=self.parse,
                            dont_filter=True
                            )
                ]

    def parse(self, response):
        years = response.xpath('//select[@name="year"]/option/text()').extract()
        categories = response.xpath('//select[@name="category"]/option/text()').extract()
        categories = [c for c in categories if 'Committee' in c or 'committee' in c] # [c for c in categories if 'cat' in c.lower()]
        
        for category in categories:
            # for year in years:
            for year in ['2013']:
                yield FormRequest('http://lso.legislature.idaho.gov/MediaArchive/ShowMediaByCommittee.do',
                                formdata={'year': year, 'category': category, 'committeeId': ''},
                                callback=self.parsenext,
                                meta={'year': year, 'category': category},
                                dont_filter=True)

    def parsenext(self, response):
        committees = list(zip(response.xpath('//select[@name="committeeId"]/option/@value').extract()[1:], response.xpath('//select[@name="committeeId"]/option/text()').extract()[1:]))
        year = response.meta.get('year')
        category = response.meta.get('category')
        
        if category == 'Joint Finance-Appropriations Committee (JFAC)':
            yield FormRequest('http://lso.legislature.idaho.gov/MediaArchive/ShowCommitteeOrMedia.do',
                            formdata={'year': year, 'category': category},
                            callback=self.parseitems,
                            meta={'committee': category, 'year': year, 'category': category},
                            dont_filter=True)
        else:
            for committee in committees:
                yield FormRequest('http://lso.legislature.idaho.gov/MediaArchive/ShowMediaByCommittee.do',
                                formdata={'year': year, 'category': category, 'committeeId': committee[0]},
                                callback=self.parseitems,
                                meta={'committee': committee[1], 'year': year, 'category': category},
                                dont_filter=True)

    def parseitems(self, response):
        dates = response.xpath('//table[@class="userTable"]/tr/td[1]/text()').extract()
        files = response.xpath('//table[@class="userTable"]/tr/td[4]/a[contains(text(), "Minutes")]/@href | //table[@class="userTable"]/tr/td[4][contains(text(), "No Minutes Posted")]/text()').extract()
        rows = list(zip(dates, files))

        for date, file in rows:
            file = file.strip() if 'No Minutes Posted' in file else response.urljoin(file)
            yield Request(file if 'No Minutes Posted' not in file else response.url, # here just re-request self
                        callback=self.parsesave,
                        meta={'committee': response.meta.get('committee'), 'date': date, 'year': response.meta.get('year'), 'category': response.meta.get('category'), 'download_timeout': 3500},
                        dont_filter=True)

    def parsesave(self, response):
        # date = response.meta.get('date')
        # committee = response.meta.get('committee')

        # filename = response.url.split('/')[-1] if '.pdf' in response.url else '{} {} {}{}'.format(date, 'No Minutes Posted', committee, '.htm')
        # os.makedirs('./idaho/', exist_ok=True)
        # with open('./idaho/' + filename, 'wb') as f:
            # f.write(response.body)

        # yield IdahoItem(committee=committee, date=date, filename=filename)

        date = response.meta.get('date')
        url = response.url
        html = ''
        state = 'idaho'
        md5 = hashlib.md5(response.body).hexdigest()
        session = response.meta.get('year')
        chamber = response.meta.get('category')
        chamber = chamber.split()[0].strip(', ')
        topic = '#TODO'
        bill_name = '#TODO'

        # text from pdf
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        pdf_text = convert_pdf_to_txt(bfr) if response.url.strip()[-4:].lower() == '.pdf' else None # 'unsupported file'

        # recognized text (OCR) from pdf
        recognized_text = []
        if pdf_text is not None and len(pdf_text.strip()) <= 50:
            with wi(filename=response.url, resolution=200) as pdf:
                pdfImage = pdf.convert('jpeg')
                imageBlobs = []
                for img in pdfImage.sequence:
                    with wi(image = img) as imgPage:
                        imageBlobs.append(imgPage.make_blob('jpeg'))
                        
            for imgBlob in imageBlobs:
                im = Image.open(io.BytesIO(imgBlob))
                text = pytesseract.image_to_string(im, lang = 'eng')
                recognized_text.append(text)

            recognized_text = '\n\n\n'.join(recognized_text)

        recognized_text = recognized_text if recognized_text else 'No Minutes Posted' # this is for add text to csv if recognized_text = []
        pdf_text = pdf_text if pdf_text is not None and len(pdf_text.strip()) > 50 else recognized_text # None if pdf_text is None

        yield IdahoItem(date=date, url=url,
                        html=html, md5=md5,
                        state=state, session=session,
                        chamber=chamber, topic=topic,
                        bill_name=bill_name, text=pdf_text)
