from bs4 import BeautifulSoup
import traceback
import requests
import time
import os




class Download_Templates:
    def __init__(self):
        self.topic_counter = 130
        self.path = os.getcwd()
        if not os.path.exists('%s/templates' %self.path):
            os.makedirs('%s/templates' %self.path)
        self.complete_path = '%s/templates' %self.path


    def Request(self, url):
        time.sleep(1)
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
            page = requests.get(url, headers=headers)
            return page.content
        except:
            return None


    def write_data(self, page, topic):
        f = open('%s/%d.html' %(self.complete_path, topic), 'wb')
        f.write(page)
        f.close()

    def write_data_pagination(self, page, topic, pagination):
        f = open('%s/%d-%d.html' %(self.complete_path, topic, pagination), 'wb')
        f.write(page)
        f.close()

    def main(self):
        print('**************  Script Is Running  **************\n')

        #go to thread ------------------
        for topic in range(100, 425295):
            try:
                url = 'https://forum.antichat.ru/threads/%d' %topic
                page = self.Request(url)

                #getting pagination number----
                try:
                    soup = BeautifulSoup(page, 'html.parser')
                    pagi = int(soup.select_one('.pageNavHeader').text.split()[-1]) 
                except:
                    pagi = 0

                self.write_data(page, topic)
                print('%d done..!' %topic)

                #if there is no pagination then continue----
                if pagi == 0:
                    continue
            except:
                traceback.print_exc()
                continue


            #for pagination ------------------
            pagination_counter = 20
            for pagination in range(2, int(pagi)):
                try:
                    p_url = 'https://forum.antichat.ru/threads/%d/page-%d' %(topic, pagination_counter)
                    page = self.Request(p_url)

                    if page == None:
                        break

                    self.write_data_pagination(page, topic, pagination)
                    print('%d-%d done..!' %(topic, pagination))
                    pagination_counter += 20
                except:
                    traceback.print_exc()
                    continue


obj = Download_Templates()
obj.main()
        
        
