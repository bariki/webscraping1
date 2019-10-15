from gsmarena.items import GsmarenaItem
from scrapy import Spider
from scrapy import Request
import re
import mysql.connector
import dateparser

class GsmarenaSpider(Spider) :

    name = 'gsmarena_spider'
    allowed_domains = ['www.gsmarena.com']
    start_urls = ['https://www.gsmarena.com/']

    def getCursor(self):
        dbCon = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="python2"
        )
        cursor = dbCon.cursor()    
        return dbCon, cursor

    def parse(self, response) :
        
        phone_divs = response.xpath('*//div[@class="module module-rankings s3"]')[0:2]

        links = phone_divs[0].xpath('./table/tbody//a/@href').extract()
        links += phone_divs[1].xpath('./table/tbody//a/@href').extract()

        for i,link in enumerate(links):
            print("Before Yield" + str(i+1))
            print('https://www.gsmarena.com/'+link)
            print("*"*100)
            yield Request('https://www.gsmarena.com/'+link, callback=self.parse_phone_detail_page)
        
        return super().parse(response)

    def parse_phone_detail_page(self, response):
        
        phone_name = response.xpath('*//h1/text()').extract_first()

        # print(phone_name)
        # print("#"*100)
        # print(response.url)
        # print("#"*100)

        display_size = response.xpath('*//li[@class="help accented help-display"]/strong/span/text()').extract_first()
        display_size = float( re.findall('[0-9.]+', display_size)[0] )

        display_pixel = response.xpath('*//li[@class="help accented help-display"]/div/text()').extract_first()
        display_pixel = re.findall('[0-9.]+', display_pixel)
        display_pixel_width = int( display_pixel[0] )
        display_pixel_height = int( display_pixel[1] )

        video_pixel = response.xpath('*//li[@class="help accented help-camera"]/div/text()').extract_first()
        back_camera_px = int(response.xpath('*//li[@class="help accented help-camera"]/strong/span/text()').extract_first())
        battery_mah = int(response.xpath('*//li[@class="help accented help-battery"]/strong/span/text()').extract_first())
        processor = response.xpath('*//li[@class="help accented help-expansion"]/div/text()').extract_first()
        
        ram = response.xpath('*//li[@class="help accented help-expansion"]/strong/span/text()').extract_first()
        ram  = re.findall('\d+',ram)[::-1]
        ram1  = ram[0]
        try:
            ram2  = ram[1]
        except:
            ram2 = 0

        gsmarena_views = response.xpath('*//li[@class="light pattern help help-popularity"]/span/text()').extract_first()
        gsmarena_views = ''.join(re.findall('\d+',gsmarena_views))

        gsmarena_likes = int(response.xpath('*//li[@class="light pattern help help-fans"]/a/strong/text()').extract_first())

        price_string = response.xpath('*//td[@data-spec="price"]/text()').extract_first()
        if( len( response.xpath('*//td[@data-spec="price"]/a/text()') ) > 0 ) :
            price_string = response.xpath('*//td[@data-spec="price"]/a/text()').extract_first()

        front_camera_px = response.xpath('*//td[@data-spec="cam2modules"]/text()').extract_first()
        front_camera_px = int(re.findall('\d+',front_camera_px)[0])

        sql = "INSERT INTO phones (company, phone_name, display_size, display_pixel_width, display_pixel_height, video_pixel, back_camera_px, battery_mah, processor, ram1, ram2, gsmarena_views, gsmarena_likes, front_camera_px, price_string)"
        sql += "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (phone_name.split()[0], phone_name, display_size, display_pixel_width, display_pixel_height, video_pixel, back_camera_px, battery_mah, processor, ram1, ram2, gsmarena_views, gsmarena_likes, front_camera_px,price_string,)
        
        dbCon, cursor = self.getCursor()
        cursor.execute(sql, val)
        dbCon.commit()
        phone_id = cursor.lastrowid
        #dbCon.close()

        for temp1 in range(0,3):
            review_link = response.xpath('*//li[@class="article-info-meta-link light"]')[temp1].xpath('./a/@href').extract_first()
            if( review_link.count('reviews') != 0 ) :
                yield Request('https://www.gsmarena.com/'+review_link, meta={'phone_id': phone_id}, callback=self.parse_review_page)

        # review_link = response.xpath('*//li[@class="article-info-meta-link light"]')[2].xpath('./a/@href').extract_first()
        

    def parse_review_page(self, response):

        dbCon, cursor = self.getCursor()
        
        coms = response.xpath('*//div[@class="user-thread"]')
        coms_count = len(coms)
        phone_id = response.meta['phone_id']

        for i,com in enumerate(coms):
            com_text = coms[i].xpath('./p/text()').extract_first()
            com_name = coms[i].xpath('./ul/li[@class="uname"]/a/b/text()').extract_first()
            com_time = coms[i].xpath('./ul/li[@class="upost"]/time/text()').extract_first()
            com_location = coms[i].xpath('./ul/li[@class="ulocation"]/span/text()').extract_first()

            sql = "INSERT INTO comments (phone_id, com_user, com_time, com_loc, com_text) VALUES (%s, %s, %s, %s, %s)"
            val = (phone_id, com_name, dateparser.parse(com_time), com_location, com_text,)
            cursor.execute(sql, val)
        
        dbCon.commit()
        dbCon.close()

        next_url = response.xpath('*//div[@class="nav-pages"]/a[@title="Next page"]/@href').extract_first()

        if( next_url != '' ):
               yield Request('https://www.gsmarena.com/'+next_url, meta={"phone_id": phone_id}, callback=self.parse_review_page)

        
        
    


