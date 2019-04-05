# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl southdakota -s LOG_FILE=scrapy_southdakota.log -s RETRY_ENABLED=True -s RETRY_TIMES=50 -s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=3 -t csv -o - > southdakota.csv
"""
import io
import hashlib
import re
import os
from bs4 import BeautifulSoup
import scrapy
from legis.items import SouthdakotaItem
from legis.read_data import convert_pdf_to_txt
from PIL import Image
import pytesseract
from wand.image import Image as wi


class SouthdakotaSpider(scrapy.Spider):
    name = 'southdakota'
    allowed_domains = ['sdlegislature.gov']
    start_urls = [ # 'http://sdlegislature.gov/Legislative_Session/archive.aspx',
                  'http://sdlegislature.gov/Interim/Archive.aspx' 
                ]

    def parse(self, response):
        committees = response.xpath('//table[@id="tblSessionArchive"]/td/a[text()="Committees"]/@href').extract()
        committees_interim = response.xpath('//td/a[text()="Committees"]/@href').extract() if 'Interim' in response.url else []

        comm_interim_new = [c for c in committees_interim if 'index.htm' not in c]
        comm_interim_old = [c for c in committees_interim if 'index.htm' in c]

        comms_new = [c for c in committees if 'comm.htm' not in c]
        comms_old = [c for c in committees if 'comm.htm' in c]

        for comm in comms_new:
            yield response.follow(comm, self.parse_comm, meta={'year': comm.split('=')[-1], 'section': 'session'})
        
        for comm in comms_old:
            yield response.follow(comm, self.parse_comm_old, meta={'year': comm.split('/')[-2], 'section': 'session'})

        for comm in comm_interim_new:
            yield response.follow(comm, self.parse_comm_interim_new, meta={'year': comm.split('=')[-1], 'section': 'interim' })
        
        for comm in comm_interim_old:
            if '2006' or '2007' not in comm: # 2006, 2007 are with server error
                yield response.follow(comm, self.parse_comm_interim_old, meta={'year': comm.split('/')[-2], 'section': 'interim', 'dont_redirect': '2003' in comm})
                
    def parse_comm_interim_new(self, response):
        comm_interim_minutes_list = response.xpath('//div[@id="ctl00_ContentPlaceHolder1_BlueBoxLeft"]/a/@href').extract()
        for comm_interim_minutes in comm_interim_minutes_list:
            yield response.follow(comm_interim_minutes, self.parse_interim_minutes, meta=response.meta)

    def parse_interim_minutes(self, response):
        doc_minutes = response.xpath('//table[@class="table"]/tbody/tr/td/a[contains(translate(text(), "MINUTE", "minute"), "minute" )]/@href|//a[@class="btn btn-default" and contains(text(), "Minute")]/@href').extract()
        for doc_minute in doc_minutes:
            yield response.follow(doc_minute, self.parse_save_all, meta=response.meta)
#-----
    def parse_save_all(self, response):
        # folder = './south_dakota/{}/{}/'.format(response.meta.get('section'), response.meta.get('year'))
        filename = response.url.split('/')[-1]
        # os.makedirs(folder, exist_ok=True)
        # with open(folder + filename, 'wb') as f:
            # f.write(response.body)
        # yield SouthdakotaItem(url=response.url)

        url = response.url
        state = 'south dakota'
        session = response.meta.get('year')
        md5 = hashlib.md5(response.body).hexdigest()

        # chamber calculations
        chambers = ['House', 'Senate', 'Joint']
        f = filename[3] if session != '1999' else filename[0]
        chamber = response.meta.get('section')
        chamber = chamber.capitalize() if chamber == 'interim' else ''.join(list(filter(lambda x: x.startswith(f.upper()), chambers)))

        # date calculations
        s = filename
        d = s if not s[0].isdigit() and not s.lower().startswith('doc1') and not s.lower().startswith('goa') and not s.lower().startswith('rul') else ''
        m = re.search("\d", d)
        first_digit = m.start() if m else None
        date = d[first_digit:first_digit+4] + session if first_digit else ''
        date = date if not date.endswith('s') else date[:-1]
        date = date[:2] + '/' + date[2:4] + '/' + date[4:]

        topic = '#TODO'

        html = response.body if filename[-4:].lower() == '.htm' else ''

        text = ''

        if filename[-4:].lower() == '.pdf':
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
            text = pdf_text
        elif filename[-4:].lower() == '.htm':
            soup = BeautifulSoup(response.text, 'html5lib')
            for script in soup(["script", "style"]):
                script.extract() # remove script and style tags
            text = soup.get_text()

        regex = r'[HSC]{1,1}[BMSPCRJ]{1,1}[RB]{0,1}[ ]{1,3}[0-9]{1,4}'
        bill_name = ', '.join(list(set(re.findall(regex, text))))

        yield SouthdakotaItem(url=url, state=state,
                              session=session, md5=md5,
                              chamber=chamber, date=date,
                              topic=topic, html=html,
                              text=text, bill_name=bill_name)
#-----
    def parse_comm_interim_old(self, response):
        minutes_section = response.xpath('//a[contains(@href, "MinutesAgendas.htm")]/@href').extract_first()
        yield response.follow(minutes_section, self.parse_minutes_interim_old, meta={'year': response.meta.get('year'), 'section': 'interim'})

    def parse_minutes_interim_old(self, response):
        comm_list = response.xpath('//table[@width]/tr/td/a[text() and contains(@href, "MinutesAgendas")]/@href').extract()
        for comm in comm_list:
            yield response.follow(comm, self.parse_comm_minutes_interim_old, meta=response.meta)
    
    def parse_comm_minutes_interim_old(self, response):
        minutes_interim_old_list = response.xpath('//a[contains(@href, "minutes/")]/@href').extract()
        for minutes_interim_old in minutes_interim_old_list:
            yield response.follow(minutes_interim_old, self.parse_save_all, meta=response.meta)

    def parse_comm(self, response):
        comm_minutes_list = response.xpath('//div[@id="ctl00_ContentPlaceHolder1_Committees_divCommittees"]/a/@href').extract()
        for comm_minutes in comm_minutes_list:
            yield response.follow(comm_minutes, self.parse_minutes, meta=response.meta)
    
    def parse_minutes(self, response):
        htm_minutes = response.xpath('//div[@id="ctl00_ContentPlaceHolder1_divMinutesAccordian"]/div/div/h4[@importfile]/@importfile').extract()
        for htm_minute in htm_minutes:
            yield response.follow(htm_minute, self.parse_save_all, meta=response.meta)
        
    def parse_comm_old(self, response):
        committees = response.xpath('//frame[contains(@title, "Senate") or contains(@title, "House")]/@src').extract()
        for committee in committees:
            yield response.follow(committee, self.parse_comm_list_old, meta=response.meta)

    def parse_comm_list_old(self, response):
        committee_list = response.xpath('//center/a/@href').extract()
        for committee_el in committee_list:
            yield response.follow(committee_el, self.parse_comm_page_old, meta=response.meta)

    def parse_comm_page_old(self, response):
        minutes_journals = response.xpath('//center/a[text()="Journals" or text()="Minutes"]/@href').extract()
        for mj in minutes_journals:
            yield response.follow(mj, self.parse_mj_page_old, meta=response.meta)

    def parse_mj_page_old(self, response):
        mj_links = response.xpath('//frame[@name="datelist"]/@src').extract()
        for mj_link in mj_links:
            yield response.follow(mj_link, self.parse_mj_dates_page_old, meta=response.meta)

    def parse_mj_dates_page_old(self, response):
        min_jrn_list = response.xpath('//a[@target="Journal" or @target="minute"]/@href').extract()
        for min_jrn in min_jrn_list:
            yield response.follow(min_jrn, self.parse_save_all, meta=response.meta)
