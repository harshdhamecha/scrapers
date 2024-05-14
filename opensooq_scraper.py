"""
	@author      harsh-dhamecha
	@email       harshdhamecha10@gmail.com
	@create date 08-08-2023 11:02:24
	@modify date 14-05-2024 16:40:47
	@desc        A script to scrape vehicle images from opensooq.
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


class OpensooqScraper(object):

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
            By.CSS_SELECTOR, 'img.image-gallery-thumbnail-image'
        )))
        img_srcs = [img.get_attribute('src') for img in imgs]
        self.img_srcs = [img_src.replace('/0x240/', '/2048x0/') for img_src in img_srcs]


    @exception_handler
    def get_page_info(self):
        anchors = WebDriverWait(self.driver, self.short_wait).until(EC.presence_of_all_elements_located((
            By.CSS_SELECTOR, 'a.p-16.blackColor.radius-8.grayHoverBg.ripple.boxShadow2.relative.block'
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

            page_text = f'?page={page}' if page > 1 else ''
            url = f'{self.base_url}{page_text}'
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
    parser.add_argument('--driver-path', type=str, default='', help='downloaded images save directory')
    parser.add_argument('--save-dir', type=str, default='./images', help='downloaded images save directory')
    parser.add_argument('--base-url', type=str, default='https://sa.opensooq.com/en/cars/cars-for-sale', help='an internet archive url')
    parser.add_argument('--short-wait', type=int, default=5, help='shorter waits in seconds')
    parser.add_argument('--name', type=str, default='Saudi-Arabia', help='country name whose data to be scraped')
    parser.add_argument('--start-page', type=int, default=51, help='nth page to start scraping from')
    parser.add_argument('--n-pages', type=int, default=20, help='total pages to be scraped')
    args = parser.parse_args()
    
    return args


if __name__ == "__main__":

    args = parse_args()
    scraper = OpensooqScraper(args)
    scraper()

