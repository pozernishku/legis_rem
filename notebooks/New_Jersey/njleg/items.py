# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NjlegItem(scrapy.Item):
    bill = scrapy.Field()
    committee = scrapy.Field()
    session = scrapy.Field()
    text = scrapy.Field()
    url = scrapy.Field()
    filename = scrapy.Field()
    date = scrapy.Field()
