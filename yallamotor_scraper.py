"""
	@author      harsh-dhamecha
	@email       harshdhamecha10@gmail.com
	@create date 29-08-2023 09:02:43
	@modify date 29-08-2023 11:39:54
	@desc        A script to scrape vehicles images from Yallamotor.com
"""


import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import requests
from io import BytesIO
from PIL import Image
from tqdm import tqdm
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class YallamotorScraper(object):

    def __init__(self, args):
        self.driver = webdriver.Firefox(service=Service(executable_path=args.driver_path))
        self.save_dir = os.path.join(args.save_dir, args.name)
        os.makedirs(self.save_dir, exist_ok=True)
        self.base_url = args.base_url
        self.short_wait = args.short_wait
        self.name = args.name
        self.start_page = args.start_page
        self.n_pages = args.n_pages
        self.end_page = self.start_page + self.n_pages + 1
   

    def exception_handler(func):

        def inner_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except NoSuchElementException:
                print('Can not locate an element in web page')
            except TimeoutException:
                print('Waited for element to be located but timed out')
            except Exception as e:
                print(f'Exception occurred - {e}')

        return inner_function
    

    @exception_handler
    def get_img_srcs(self):
        imgs = WebDriverWait(self.driver, self.short_wait).until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, 'img.img-main'
        )))
        self.img_srcs = [img.get_attribute('src') for img in imgs]


    @exception_handler
    def get_page_info(self):
        anchors = WebDriverWait(self.driver, self.short_wait).until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, 'a.black-link'
        )))
        self.vehicle_srcs = [anchor.get_attribute('href') for anchor in anchors]


    @exception_handler
    def save_image(self, url, filepath):

        r = requests.get(url, verify=False).content
        img = Image.open(BytesIO(r)).convert("RGB")
        img.save(filepath)


    @exception_handler
    def __call__(self):

        for page in tqdm(range(self.start_page, self.end_page)):

            page_text = f'page={page}' if page > 1 else ''
            url = f'{self.base_url}search?{page_text}sort=updated_desc'
            self.driver.get(url)
            self.get_page_info()

            for i, vehicle_src in enumerate(self.vehicle_srcs):

                self.driver.get(vehicle_src)
                self.get_img_srcs()

                for j, img_src in enumerate(self.img_srcs):

                    img_name = f'{self.name}_{page}_{str(i)}_{str(j)}.jpg'
                    path = os.path.join(self.save_dir, img_name)
                    self.save_image(img_src, path)

        self.driver.close()


def parse_args():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--driver-path', type=str, default='../../extras/geckodriver-v0.33.0-linux32/geckodriver', help='downloaded images save directory')
    parser.add_argument('--save-dir', type=str, default='/media/harsh/Data/LPR/data/scraped/yallamotor', help='downloaded images save directory')
    parser.add_argument('--base-url', type=str, default='https://oman.yallamotor.com/used-cars/', help='an internet archive url')
    parser.add_argument('--short-wait', type=int, default=5, help='shorter waits in seconds')
    parser.add_argument('--name', type=str, default='Oman', help='country name whose data to be scraped')
    parser.add_argument('--start-page', type=int, default=1, help='nth page to start scraping from')
    parser.add_argument('--n-pages', type=int, default=20, help='total pages to be scraped')
    args = parser.parse_args()
    
    return args


if __name__ == "__main__":

    args = parse_args()
    scraper = YallamotorScraper(args)
    scraper()

