import scrapy
from njleg.items import NjlegItem
import os

import re

class NjlegSpider(scrapy.Spider):
    name = "njleg"
    domain = "http://www.njleg.state.nj.us/legislativepub/"
    pdf_dir = "pdf_files"
    history = []

    def __init__(self):
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)

    def start_requests(self):
        yield scrapy.Request(url="http://www.njleg.state.nj.us/legislativepub/pubhear.asp", callback=self.parse_sessions)

    def parse_sessions(self, response):
        sessions = response.xpath("//a[@class='blk2']")

        for session in sessions:
            request = scrapy.Request(url=self.domain + self.validate(session.xpath("./@href")), callback=self.parse_committee)
            request.meta['session'] = self.validate(session.xpath("./text()"))
            yield request

    def parse_committee(self, response):
        committees = response.xpath("//table[@bgcolor='#F4F4F4']//ul//li")
        if len(committees) == 0:
            committees = response.xpath("//table[@width='100%']//ul//li")

        for committee in committees:
            html_str = committee.extract()
            temp = [tp.split('<')[0].strip() for tp in html_str.split('>')[1:]]
            label_list = []
            for item in temp:
                if item == '': 
                    continue
                label_list.append(" ".join([tp.strip() for tp in item.split(" ") if tp.strip()!= ""]))
            label_tp_list = []
            flag = 0
            for item in label_list:
                if 'of' in item or 'before' in item or 'Meeting' in item:
                    flag = 1
                if flag == 1:
                    label_tp_list.append(item)
                if 'COMMITTEE' in item:
                    label_tp_list.append(item)
                    flag = 0
                    break
            if flag == 1:
                committee_label = " ".join(label_tp_list[:2]) if len(label_tp_list) > 1 else ''
            else:
                committee_label = " ".join(label_tp_list)
            
            html_str = committee.extract()
            try:
                html_str = " ".join([tp.strip() for tp in html_str.split(' ') if tp.strip()!=''])
                date = re.search("\w+[ ]*\d+[ ]*,\W\d{4}", html_str).group(0)
            except:
                html_str = committee.xpath('..//strong').extract()
                if len(html_str) == 0:
                    html_str = committee.xpath('..//b').extract()
                html_str = " ".join([tp.strip() for tp in ' '.join(html_str).split(' ') if tp.strip()!=''])
                try:
                    date = re.search("\w+[ ]*\d+[ ]*,\W\d{4}", html_str).group(0)
                except:
                    date = ''
            date = " ".join([tp.strip() for tp in date.split(' ') if tp.strip()!='']).replace(",,", ",")
            date = date.split(">")[-1] if '>' in date else date

            download_urls = committee.xpath('.//a')
            if len(download_urls) == 0:
                download_urls = committee.xpath('..//a')
            for url_tp in download_urls:
                if self.validate(url_tp.xpath('./text()')) in ['hearing', 'appendix', 'HTML']:
                    url = self.domain + self.validate(url_tp.xpath('./@href'))
                    if url not in self.history:
                        request = scrapy.Request(url=url, callback=self.save_pdf)
                        request.meta['session'] = response.meta['session']
                        request.meta['committee'] = committee_label
                        request.meta['date'] = date
                        request.meta['filename'] = url.split('/')[-1].split(',')[0].strip()
                        
                        item = NjlegItem()
                        item['session'] = " ".join([tp.strip() for tp in request.meta['session'].split(' ') if tp.strip() != ''])
                        item['committee'] = request.meta['committee']
                        item['date'] = request.meta['date']
                        item['url'] = request.url
                        item['filename'] = request.meta['filename']

                        try:
                            yield request
                        except:
                            pass
 
    def save_pdf(self, response):
        item = NjlegItem()

        if 'pdf' in response.meta['filename']:
            with open("%s/%s" % (self.pdf_dir, response.meta['filename']), "wb") as fp:
                fp.write(response.body)
        else:
            item['text'] = response.body
        item['session'] = " ".join([tp.strip() for tp in response.meta['session'].split(' ') if tp.strip() != ''])
        item['committee'] = response.meta['committee']
        item['date'] = response.meta['date']
        item['url'] = response.url
        item['filename'] = response.meta['filename']
        yield item

    def validate(self, xpath_obj):
        try:
            return " ".join([tp.strip() for tp in xpath_obj.extract_first().strip().split(' ') if tp.strip()!=''])
        except:
            return ""