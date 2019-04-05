# -*- coding: utf-8 -*-
"""
How to run spider.
- Go to legis project directory
- Run: scrapy crawl arkpdf -t csv -o - > arkansas.csv
"""
import hashlib
import scrapy, os, json
from scrapy.http.request import Request
import io
from PIL import Image
import pytesseract
from wand.image import Image as wi
from scrapy.http import FormRequest
from legis.items import ArkpdfItem
from legis.read_data import convert_pdf_to_txt, document_to_text


class ArkpdfSpider(scrapy.Spider):
    name = 'arkpdf'
    allowed_domains = ['www.arkleg.state.ar.us']

    def start_requests(self):
        with open('./params/asp.json', encoding='utf-8') as f:
            asp = json.loads(f.read())

        return [FormRequest('http://www.arkleg.state.ar.us/assembly/2017/2017R/Pages/MeetingsAndEventsCalendar.aspx?listview=month',
                            formdata = {
                                        'MSOTlPn_View': '0',
                                        'MSOTlPn_ShowSettings': 'False',
                                        'MSOTlPn_Button': 'none',
                                        '__REQUESTDIGEST': 'InvalidFormDigest',
                                        'MSOSPWebPartManager_DisplayModeName': 'Browse',
                                        'MSOSPWebPartManager_ExitingDesignMode': 'false',
                                        'MSOSPWebPartManager_OldDisplayModeName': 'Browse',
                                        'MSOSPWebPartManager_StartWebPartEditingName': 'false',
                                        'MSOSPWebPartManager_EndWebPartEditing': 'false',
                                        '_maintainWorkspaceScrollPosition': '0',
                                        '__VIEWSTATE': asp.get('viewstate'),
                                        '__VIEWSTATEGENERATOR': '90E54CD0',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_startDateBox_Raw': '1104537600000',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$startDateBox': '1/1/2005',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_startDateBox_DDDWS': '0:0:12000:462:219:1:257:248:1:0:0:0',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_startDateBox_DDD_C_FNPWS': '0:0:12000:546:224:0:-10000:-10000:1:0:0:0',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$startDateBox$DDD$C': '01/01/2005:01/01/2005',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_endDateBox_Raw': '1924905600000',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$endDateBox': '12/31/2030',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_endDateBox_DDDWS': '0:0:12000:751:219:1:257:248:1:0:0:0',
                                        'ctl00_m_g_ef209707_6a54_4d40_a8d4_0b2684eb8af9_ctl00_endDateBox_DDD_C_FNPWS': '0:0:12000:835:224:0:-10000:-10000:1:0:0:0',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$endDateBox$DDD$C': '12/01/2030:12/31/2030',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$cbPanel$ctl09$DXKVInput': '[]',
                                        'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$cbPanel$ctl09$CallbackState': asp.get('callbackstate'),
                                        'DXScript': '1_142,1_80,1_135,1_98,1_105,1_97,1_84,1_77,1_128,1_126,1_92,1_91,1_79,1_90,1_113',
                                        '__CALLBACKID': 'ctl00$m$g_ef209707_6a54_4d40_a8d4_0b2684eb8af9$ctl00$cbPanel',
                                        '__CALLBACKPARAM': 'c0:1/1/2005,12/31/2030',
                                        '__EVENTVALIDATION': '/wEWCQL4183BCAKmgpjVCAKUlfWiBAKu0sfACgKRrN+tDgKv1PrfAwLzzNqXBwKWvualAwKBt7bpB1ltUQG/cdt1oJ/8uBxQclGG7ZtT'
                            } ) ]
    
    def parse(self, response):
        for n in response.xpath('//td[5]/a[contains(@href, "javascript")]/@onclick').extract():
            yield Request(n.split(',')[0].split('\'')[1],  callback=self.parseattach)
    
    def parseattach(self, response): 
        # date = response.xpath('//td[contains(@id, "MeetingDate")]/text()').extract_first().replace("/", "-").replace(":", "-")
        date = response.xpath('//td[contains(@id, "MeetingDate")]/text()').extract_first()
        comm = response.xpath('//td[contains(@id, "CommitteeName")]/text()').extract_first().replace('/', '-')
        agenda = response.urljoin(response.xpath('//a[text()="Agenda"]/@href').extract_first())
        minutes = response.xpath('//a[contains(translate(text(), "MINUTE", "minute"), "minute") or contains(translate(@href, "MINUTE", "minute"), "minute")]/@href').extract()
        
        for x in [agenda] + list(map(response.urljoin, minutes)):
            yield Request(x, callback=self.parsesave, meta={'date': date, 'comm': comm})

    def parsesave(self, response):
        # foldername = './arkansas/' + response.meta.get('date') + ' ' + response.meta.get('comm')
        # filename = response.url.split('/')[-1] if any([s in response.url.split('/')[-1] for s in ['minutes', 'minute', 'Minutes', 'Minute']]) else 'Agenda.pdf'
        # filename = filename.replace('%20', '-')
        # os.makedirs(foldername, exist_ok=True)
        
        # with open(foldername + '/' + filename, 'wb') as f:
        #     f.write(response.body)
        # yield ArkpdfItem(url=response.url, date=response.meta.get('date'), comm=response.meta.get('comm') )

        foldername = './arkansas/' 
        filename = response.url.split('/')[-1].replace('%20', '-').strip()
        filename = filename if 'doc' in filename[-5:] or 'odt' in filename[-5:] else ''
        path2doc = foldername + filename
        os.makedirs(foldername, exist_ok=True)
        
        if filename:
            with open(path2doc, 'wb') as f:
                f.write(response.body)

        date = response.meta.get('date')

        state = 'arkansas'

        session = date.split(' ')[0].split('/')[2] if date else ''
        slist, i, j = [], 0, 1
        for s in range(1987, 2009):
            slist.append(str(s+i) + '-' + str(s+j))
            i += 1
            j += 1
        session = [s for s in slist if session in s]
        session = session[0] if session else ''

        md5 = hashlib.md5(response.body).hexdigest()

        html = ''

        # text from pdf, doc, docx, odt
        bytesio = io.BytesIO(response.body)
        bfr = io.BufferedReader(bytesio)
        doc_pdf_text = convert_pdf_to_txt(bfr) if response.url.strip()[-4:].lower() == '.pdf' \
        else document_to_text(path2doc) if 'doc' in response.url.strip()[-4:].lower() \
        else document_to_text(path2doc) if 'odt' in response.url.strip()[-4:].lower() \
        else 'unsupported file'

        # !!! comment these lines below
        # doc_pdf_text = document_to_text(path2doc) if 'doc' in response.url.strip()[-4:].lower() \
        # else document_to_text(path2doc) if 'odt' in response.url.strip()[-4:].lower() \
        # else 'unsupported file'

        # recognized text (OCR) from pdf
        if len(doc_pdf_text.strip()) <= 5:
            pdf = wi(filename=response.url, resolution=300)
            pdfImage = pdf.convert('jpeg')
            imageBlobs = []
            for img in pdfImage.sequence:
                imgPage = wi(image = img)
                imageBlobs.append(imgPage.make_blob('jpeg'))

            recognized_text = []

            for imgBlob in imageBlobs:
                im = Image.open(io.BytesIO(imgBlob))
                text = pytesseract.image_to_string(im, lang = 'eng')
                recognized_text.append(text)

            recognized_text = '\n\n\n'.join(recognized_text)

        doc_pdf_text = doc_pdf_text if len(doc_pdf_text.strip()) > 5 else recognized_text
        
        committee = response.meta.get('comm')
        chamber = committee.split('-')[-1].strip() if committee is not None else ''
        chamber = chamber.capitalize() if 'house' == chamber.lower() or 'senate' == chamber.lower() or 'joint' == chamber.lower() else ''
        
        topic = '#TODO'

        bill_name = '#TODO'

        yield ArkpdfItem(url=response.url, date=date,
                            state=state, session=session,
                            md5=md5, html=html,
                            text=doc_pdf_text, chamber=chamber,
                            topic=topic, bill_name=bill_name )
