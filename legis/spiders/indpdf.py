# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl indpdf -s LOG_FILE=scrapy_indpdf.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=3 -t csv -o - > indpdf.csv
"""
import io
import hashlib
import json
import re
import os
import scrapy
from scrapy.http.request import Request
from legis.items import IndpdfItem
from legis.read_data import convert_pdf_to_txt
from PIL import Image
import pytesseract
from wand.image import Image as wi


class IndpdfSpider(scrapy.Spider):
    name = 'indpdf'
    allowed_domains = ['iga.in.gov']
    start_urls = ['https://iga.in.gov/solr-search/solr/select?facet=true&q=fiscal%20AND%20(sessionyear%3A2009%20OR%20sessionyear%3A2010%20OR%20sessionyear%3A2011%20OR%20sessionyear%3A2012%20OR%20sessionyear%3A2013%20OR%20sessionyear%3A2014%20OR%20sessionyear%3A2015%20OR%20sessionyear%3A2016%20OR%20sessionyear%3A2017%20OR%20type%3ACONSTITUTION)&facet.field=committeetype&facet.field=reporttype&facet.field=lawtype&facet.field=type&facet.field=billtype&facet.field=billcommittee&facet.field=chamber&facet.field=party&facet.field=sessionyear&facet.field=version_year_t&facet.limit=20&facet.mincount=1&f.topics.facet.limit=50&json.nl=map&defType=edismax&start={}&fq=type%3A%22FISCAL%22&wt=json&json.wrf=jQuery110204040444531374616_1504816516199&_=1504816516205'.format(i) for i in range(0,12441,10) ]

    numb = -1
    def parse(self, response):
        resp = json.loads(re.search('{.*}', response.text).group())
        for u in resp["response"]["docs"]:
            yield Request(response.urljoin(u["url"]), 
                          callback=self.parsepage, 
                          meta={'year': u["sessionyear"], 
                                'numbname': json.loads(u["fiscalbill"][0])["name"],
                                'topic': u["body"] } )
            
    def parsepage(self, response):
        yield Request('https://iga.in.gov/documents/' + response.xpath('//a[@class="accordion-header-1 accordion-toggle ico-pdf-dual"]/@href').extract_first().split('-')[-1] + '/download', 
                      callback=self.parsesave, 
                      meta={'year': response.meta.get('year'), 
                            'numbname': response.meta.get('numbname'), 
                            'chamber': response.url.split('/')[-2],
                            'topic': response.meta.get('topic') })

    def parsesave(self, response):
        # self.numb += 1
        # filename = response.meta.get('year') + '-' + str(self.numb) + '-' + response.meta.get('numbname') + '.pdf'
        # os.makedirs('./indiana/', exist_ok=True)

        # with open('./indiana/' + filename, 'wb') as f:
            # f.write(response.body)
        # yield IndpdfItem(url=response.url, year=response.meta.get('year'), bill=response.meta.get('numbname'))

        url = response.url
        state = 'indiana'
        html = ''
        bill_name = response.meta.get('numbname')
        session = response.meta.get('year')
        chamber = response.meta.get('chamber').capitalize()
        topic = response.meta.get('topic')
        topic = ' '.join(topic) if topic else ''
        date = '#TODO'
        md5 = hashlib.md5(response.body).hexdigest()

        # text from pdf
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        pdf_text = convert_pdf_to_txt(bfr) # if response.url.strip()[-4:].lower() == '.pdf' else 'unsupported file'

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

        yield IndpdfItem(url=url, state=state,
                         html=html, text=pdf_text,
                         bill_name=bill_name, session=session,
                         chamber=chamber, topic=topic,
                         date=date, md5=md5)
