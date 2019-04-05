# -*- coding: utf-8 -*-
import os
import hashlib
import scrapy
from legis.items import PennsylvaniaItem


class PennsylvaniaSpider(scrapy.Spider):
    name = 'pennsylvania'
    allowed_domains = ['www.legis.state.pa.us']
    start_urls = ['http://www.legis.state.pa.us/CFDOCS/Legis/TR/Public/tr_finder_public.cfm']
    base_url = "http://www.legis.state.pa.us/CFDOCS/Legis/TR/Public/tr_finder_public_action.cfm?tr_doc_typ=T&billBody=&billTyp=&billNbr=&hearing_month=&hearing_day=&hearing_year=&NewCommittee=$z$&subcommittee=&subject=&bill=&new_title=&new_salutation=&new_first_name=&new_middle_name=&new_last_name=&new_suffix=&hearing_loc="


    def parse(self, response):
        values = response.xpath('//select[@id="NewCommittee"]//option/@value').extract()

        for val in values:
            if val == '':
                continue
            val = val.replace(' ', '+')

            yield scrapy.Request(url=self.base_url.replace('$z$', val), callback=self.parse_list)

    def parse_list(self, response):
        pdf_links = response.xpath('//table[@class="DataTable"]//a/@href').extract()

        for url in pdf_links:
            if 'pdf' in url:
                yield scrapy.Request(url=url, callback=self.parse_pdf)

    def parse_pdf(self, response):
        url = response.url
        session = response.url.split('/')[-1].split('.')[0].split('_')[0]
        md5 = hashlib.md5(response.body).hexdigest()
        state = 'pennsylvania'
        date = '#TODO'
        chamber = '#TODO'
        html = ''
        text = '#TODO'
        bill_name = '#TODO'
        topic = '#TODO'

        os.makedirs('./pennsylvania/', exist_ok=True)
        with open('./pennsylvania/' + response.url.split('/')[-1], 'wb') as f:
            f.write(response.body)

        yield PennsylvaniaItem(url=url, date=date, 
                        text=text, state=state,
                        html=html, session=session, 
                        md5=md5, chamber=chamber,
                        topic=topic, bill_name=bill_name)
