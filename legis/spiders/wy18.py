# -*- coding: utf-8 -*-
import hashlib
import os
import re
import io
import scrapy
from legis.items import WyomingItem
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
from wand.image import Image as wi
from legis.read_data import convert_pdf_to_txt



class Wy18Spider(scrapy.Spider):
    name = 'wy18'
    allowed_domains = ['legisweb.state.wy.us']
    start_urls = ['http://legisweb.state.wy.us/LSOWEB/Interim.aspx/']

    def parse(self, response):
        refs_2008_2001 = response.xpath('//a[contains(@href, "intcomm.htm")]/@href').extract()
        for ref200_ in refs_2008_2001[7:8]: # change the years range
            yield response.follow(ref200_, callback=self.parse_ref200_, meta={'year': ref200_.split('/')[1] })

    def parse_ref200_(self, response):
        comm_refs = response.xpath('//div[@id="content"]//a/@href').extract()
        for comm_ref in comm_refs:
            yield response.follow(comm_ref, callback=self.parse_comm, meta=response.meta)

    def parse_comm(self, response):
        minutes_refs = response.xpath('//a[contains(translate(text(), "MINUTES", "minutes"), "minutes")]/@href').extract()
        for minutes_ref in minutes_refs:
            yield response.follow(minutes_ref, callback=self.parse_mins, meta=response.meta)

    def parse_mins(self, response):
        mins_refs = response.xpath('//a[contains(translate(@href, "MINUTES", "minutes"), "minutes")]/@href').extract()
        for min_ref in mins_refs:
            yield response.follow(min_ref, callback=self.parse_save, meta=response.meta)
    
    def parse_save(self, response):
        md5 = hashlib.md5(response.body).hexdigest()
        filename = response.url.split('/')[-1]

        os.makedirs('./wy/', exist_ok=True)
        with open('./wy/' + md5 + ' ' + filename, 'wb') as f:
            f.write(response.body)

        session = response.meta.get('year')

        state = 'wyoming'

        topic = '#TODO'

        url = response.url

        date_part = re.findall('[0-9]{4}', filename)
        date = date_part[0] if len(date_part) > 0 else ''
        date = session + '/' + date[:2] + '/' + date[-2:] if date else '' # two dates in pdf files are not correct

        chamber = '#TODO'

        html = response.body if filename[-4:].lower() == '.htm' else ''
        
        text = ''
        if filename[-4:].lower() == '.htm':
            soup = BeautifulSoup(response.text)
            for script in soup(["script", "style"]):
                script.extract() # remove script and style tags
            text = soup.get_text()
        elif filename[-4:].lower() == '.pdf':
            # text from pdf
            bytesio = io.BytesIO(response.body)
            bfr = io.BufferedReader(bytesio)
            text = convert_pdf_to_txt(bfr) # if response.url.strip()[-4:].lower() == '.pdf' else 'unsupported file'

            # recognized text (OCR) from pdf
            if len(text.strip()) <= 50:
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

            text = text if len(text.strip()) > 50 else recognized_text


        bill_name = '#TODO'
        
        yield WyomingItem(md5=md5, session=session,
                          state=state, topic=topic,
                          url=url, date=date,
                          chamber=chamber, html=html,
                          text=text, bill_name=bill_name
                          )