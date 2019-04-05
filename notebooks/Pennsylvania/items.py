# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LegisItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class MontanaItem(scrapy.Item):
    url = scrapy.Field()
    # year = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    state = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    topic = scrapy.Field()

class PennsylvaniaItem(scrapy.Item):
    url = scrapy.Field()
    # year = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    state = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    topic = scrapy.Field()

class SouthdakotaItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()

class HawaiiItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()

class ArkpdfItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()
    
    # url = scrapy.Field()
    # date = scrapy.Field()
    # comm = scrapy.Field()


class ColspiderItem(scrapy.Item):
    url = scrapy.Field()

class ColarchItem(scrapy.Item):
    url = scrapy.Field()
    
class ConspiderItem(scrapy.Item):
    url = scrapy.Field()

class FlopdfItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()

    # url = scrapy.Field()
    # url_all = scrapy.Field()
    # filename = scrapy.Field()
    # folder = scrapy.Field()

class IdahoItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()


    # committee = scrapy.Field()
    # date = scrapy.Field()
    # filename = scrapy.Field()

class IndpdfItem(scrapy.Item):
    url = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    bill_name = scrapy.Field()
    session = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    date = scrapy.Field()
    md5 = scrapy.Field()

    # url = scrapy.Field()
    # year = scrapy.Field()
    # bill = scrapy.Field()

class MaineItem(scrapy.Item):
    url = scrapy.Field()
    date = scrapy.Field()
    text = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    session = scrapy.Field()
    md5 = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    bill_name = scrapy.Field()
    
    # bill = scrapy.Field()
    # name = scrapy.Field()
    # filename = scrapy.Field()
    # url = scrapy.Field()

class MnItem(scrapy.Item):
    url = scrapy.Field()
    date = scrapy.Field()
    text = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    session = scrapy.Field()
    md5 = scrapy.Field()
    chamber = scrapy.Field()
    topic = scrapy.Field()
    bill_name = scrapy.Field()


class NebraskaItem(scrapy.Item):
    title = scrapy.Field()
    filename = scrapy.Field()

class NydocItem(scrapy.Item):
    url = scrapy.Field()
    year = scrapy.Field()
    date = scrapy.Field()
    name = scrapy.Field()

class OhiopdfItem(scrapy.Item):
    url = scrapy.Field() #
    date = scrapy.Field() #
    text = scrapy.Field() #
    state = scrapy.Field() #
    html = scrapy.Field() #
    session = scrapy.Field() #
    md5 = scrapy.Field() #
    chamber = scrapy.Field() #
    topic = scrapy.Field() #
    bill_name = scrapy.Field() #

    organization = scrapy.Field() #
    stance = scrapy.Field() #
    # bill = scrapy.Field()
    # date = scrapy.Field()

class WyItem(scrapy.Item):
    url = scrapy.Field()
    filename = scrapy.Field()
    date = scrapy.Field()
    committee = scrapy.Field()

class IowaspItem(scrapy.Item):
    session = scrapy.Field()
    chamber = scrapy.Field()
    bill_name = scrapy.Field()
    url = scrapy.Field()
    # filename = scrapy.Field()
    state = scrapy.Field()
    html = scrapy.Field()
    text = scrapy.Field()
    md5 = scrapy.Field()
    date = scrapy.Field()
    topic = scrapy.Field()
    