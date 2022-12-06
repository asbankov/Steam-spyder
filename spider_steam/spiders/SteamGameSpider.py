import scrapy
from spider_steam.items import SpiderSteamItem
from lxml import etree
from bs4 import BeautifulSoup
import requests
import re

class SteamgamespiderSpider(scrapy.Spider):
    name = 'SteamGameSpider'
    allowed_domains = ['steampowered.com']

    def start_requests(self):
        searchRequests = ['strategies', 'anime+games', 'rpg']
        for sr in searchRequests:
            r = requests.get('https://store.steampowered.com/search/?term=' + sr)
            page = r.content.decode("utf-8")
            soup = BeautifulSoup(page, 'html.parser')
            dom = etree.HTML(str(soup))
            urls = dom.xpath('//a[@data-search-page="1" or @data-search-page="2"]/@href')
            #for url in urls:
            #    print('\n')
            #    print(url)
            #    print('\n')
            for url in urls:
                if 'https://store.steampowered.com/app/' in str(url):
                    yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        items = SpiderSteamItem()
        categories = response.xpath('//div[@class="breadcrumbs"]/*/a/text()')
        category = []
        for c in categories[1:]:
            category.append(c.extract())
        items['category'] = category

        developers = response.xpath('(//div[@class="app_header_grid_container"]/div[@class="grid_content"])[2]/a/text()')
        developer = []
        for d in developers:
            developer.append(d.extract())
        items['developer'] = developer

        tags = response.xpath('//a[@class="app_tag"]/text()')
        tagsList = []
        for t in tags:
            tagsList.append(t.extract().strip())
        items['tags'] = tagsList

        platforms = response.xpath('//div[contains(@class, "game_area_sys_req") and contains(@class, "sysreq_content")]/@data-os')
        platformsList = []
        for p in platforms:
            platformsList.append(p.extract())
        items['platforms'] = platformsList

        priceRaw = response.xpath('//div[@class="game_purchase_action_bg"]//div[contains(@class, "game_purchase_price") or @class="discount_final_price"]/text()')
        if len(priceRaw) == 0:
            items['price'] = ''
        else:
            priceRaw = priceRaw[0].extract()
            if 'Free' in priceRaw:
                items['price'] = "0"
            else:
                price = re.sub(r'\D', '', priceRaw)
                items['price'] = price
        
        name = response.xpath('//div[@class="apphub_HeaderStandardTop"]/div[@id="appHubAppName" and @class="apphub_AppName"]/text()').extract()
        date = response.xpath('//div[@class="grid_content grid_date"]/text()').extract()
        items['name'] = ''.join(name).strip()
        items['date'] = ''.join(date).strip()
        
        reviewSummary = response.xpath('//div[@class = "user_reviews_summary_bar"]//span[contains(@class, "game_review_summary")]/text()')
        if len(reviewSummary) <= 1:
            items['textRate'] = 'No reviews'
        else:
            items['textRate'] = reviewSummary[0].extract()
        
        reviewDescr = response.xpath('//div[@class = "user_reviews_summary_bar"]//span[contains(@class, "game_review_summary")]/@data-tooltip-html')
        if len(reviewDescr) <= 1:
            items['rating'] = 'No reviews'
            items['reviewsQuantity'] = '0'
        else:
            items['rating'] = reviewDescr[0].extract()
            items['reviewsQuantity'] = re.search(r'(?<=the )[\d,]+', reviewDescr[0].extract()).group(0)
        if bool(re.search(r'\d\d\d\d', items['date'])):
            if int(re.search(r'\d\d\d\d', items['date']).group(0)) >= 2000:
                #print(int(re.search(r'\d\d\d\d', items['date']).group(0)))
                yield items 
        elif items['date'] != '':
            yield items
