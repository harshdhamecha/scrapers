"""
	@author      harsh-dhamecha
	@email       harshdhamecha10@gmail.com
	@create date 23-05-2023 12:08:44
	@modify date 14-05-2024 16:41:07
	@desc        A script to scrape license plates data from numbers.ae for UAE
"""


import argparse
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NumbersUAEScraper(object):

    def __init__(self, args):
        self.driver = webdriver.Firefox(service=Service(executable_path=args.driver_path))
        self.save_dir = os.path.join(args.save_dir, args.emirate)
        self.base_url = args.base_url
        self.short_wait = args.short_wait
        self.emirate = args.emirate
        self.plate_texts = []
        self.plate_srcs = []
        self.get_mappings()
        self.url = f'{self.base_url}?AddSearch[emirate]={self.emirate_codes_patterns[self.emirate][0]}'


    def exception_handler(func):

        def inner_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except NoSuchElementException:
                print('Can not locate an element in web page')
            except TimeoutException:
                print('Waited for element to be located but timed out')
            except KeyError:
                print(f'Not a valid emirate name')
            except Exception as e:
                print(f'Exception occurred - {e}')

        return inner_function


    @exception_handler
    def get_mappings(self):
        self.emirate_codes_patterns = {
            'Dubai': ['1', r"\b[A-Z]\s\d+\b"],
            'Abu-Dhabi': ['2', r"\b\d{1,2}\s\d+\b"],
            'Ajman': ['3', r"\b[A-Z]\s\d+\b"],
            'Umm-Al-Quwain': ['4', r"\b[A-Z]\s\d+\b"],
            'Ras-Al-Khaimah': ['5', r"\b[A-Z]\s\d+\b"],
            'Sharjah': ['6', r"\b[0-9]\s\d+\b"],
            'Fujairah': ['7', r"\b[A-Z]\s\d+\b"]
        }


    @exception_handler
    def scroll_to_end(self):

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:

            time.sleep(self.short_wait)

            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(self.short_wait)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height


    @exception_handler
    def get_img_tags(self):
        img_tags = WebDriverWait(self.driver, self.short_wait).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'img')))
        self.plate_imgs = [img for img in img_tags if '/plate/' in img.get_attribute("src")]


    @exception_handler
    def extract_plate_text(self, text):
        
        match = re.search(self.emirate_codes_patterns[self.emirate][1], text)
        return match.group().replace(' ', '-') if match else None


    @exception_handler
    def get_plate_info(self):

        for img in self.plate_imgs:
            text = img.get_attribute('alt')
            plate_text = self.extract_plate_text(text)
            if plate_text:
                self.plate_texts.append(plate_text)
                self.plate_srcs.append(img.get_attribute('src'))
        

    @exception_handler
    def save_image(self, url, path):
        r = requests.get(url, verify=False).content
        with open(path, 'wb') as f:
            f.write(r)


    @exception_handler
    def __call__(self):

        os.makedirs(self.save_dir, exist_ok=True)
        
        self.driver.get(self.url)
        self.scroll_to_end()
        self.get_img_tags()
        self.get_plate_info()

        for i, plate_src in enumerate(tqdm(self.plate_srcs)):

            img_name = f'UAE_{self.emirate}_{self.plate_texts[i]}.png'
            path = os.path.join(self.save_dir, img_name)
            self.save_image(plate_src, path)

        self.driver.close()


def parse_args():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--driver-path', type=str, default='', help='downloaded images save directory')
    parser.add_argument('--save-dir', type=str, default='./images', help='downloaded images save directory')
    parser.add_argument('--base-url', type=str, default='https://www.numbers.ae/plate', help='an internet archive url')
    parser.add_argument('--short-wait', type=int, default=5, help='shorter waits in seconds')
    parser.add_argument('--emirate', type=str, help='emirate name whose data to be scraped')

    args = parser.parse_args()
    
    return args


if __name__ == "__main__":

    args = parse_args()
    scraper = NumbersUAEScraper(args)
    scraper()
