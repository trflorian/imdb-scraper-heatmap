import time

from lxml import html
from dataclasses import dataclass

import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@dataclass
class ImdbEntry:
    id: str
    title: str
    year: int
    type: str

class ImdbScraper:
    timeout = 5
    max_retries = 10
    max_episodes = 100
    base_url = 'https://www.imdb.com'
    driver = None

    def __init__(self):
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('window-size=1920x1080')

    def __enter__(self):
        self.driver = webdriver.Chrome(options=self.chrome_options)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.driver.close()

    def _restart_driver(self):
        self.driver.close()
        self.driver = webdriver.Chrome(options=self.chrome_options)

    def _load_url(self, imdb_url: str):
        print(f'Fetching from {imdb_url}')
        self.driver.implicitly_wait(5)
        self.driver.get(f'{self.base_url}/{imdb_url}')

    def _load_element(self, xpath: str):
        try:
            element_present = EC.presence_of_element_located((By.XPATH, xpath))
            WebDriverWait(self.driver, timeout=self.timeout).until(element_present)
            tree = html.fromstring(self.driver.page_source)
            matches = tree.xpath(xpath)
            if len(matches) == 0:
                return None
            return matches[0]
        except TimeoutException:
            return None

    def _find_element_initial(self, imdb_url: str, xpath: str):
        for attempt in range(self.max_retries):
            print(f'find_element attempt ({attempt+1}/{self.max_retries})')
            self._load_url(imdb_url)
            elem = self._load_element(xpath)
            if elem is None:
                self._restart_driver()
                continue
            return elem
        print('Failed to find xpath element.')
        return None

    def search(self, search_text: str, search_type: str = None):
        results = []

        # [None, 'tv', 'ft']
        type_query = ''
        if search_type is not None:
            type_query = f'&s=tt&type={search_type}'

        search_text = search_text.replace(' ', '%20')

        search_results = self._find_element_initial(
            imdb_url=f'/find?q={search_text}{type_query}',
            xpath='''//*[@id='__next']/main/div[2]/div[3]/section/div/div[1]/section[3]/div[2]'''
        )

        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[3]/div[2]/div --- if not found, this is a div
        if search_results[0].tag == 'div':
            # no results found
            return results

        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul --- if matches, ul children <= 5
        num_results = len(search_results[0])

        # individual results
        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[1]/div[2]/div[1]/a
        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[2]/div[2]/div[1]/a

        for i in range(num_results):
            li_index = i+1

            # extract href from <a> tag
            entry_id = self._load_element(
                xpath=f'//*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[{li_index}]/div[2]/div[1]/a '
            ).attrib['href'].split('/')[2]

            year_text = self._load_element(
                xpath=f'//*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[{li_index}]/div[2]/div[1]/ul[1]/li[1]/label'
            ).text
            year_splits = year_text.replace(' ', '').split('–')

            entry_type = 'ft' if len(year_splits) == 1 else 'tv'

            if search_type is not None and search_type != entry_type:
                print(f'WARNING: found an entry of type {entry_type} but search query was for type {search_type}')

            print(f'id={entry_id}, year={year_text}, splits={year_splits}')

        print(search_results)

with ImdbScraper() as sc:
    sc.search(search_text='Breaking Bad', search_type=None)


# Movie/Series to search for
query = 'Breaking Bad'
# query = 'Dark'
# query = 'Prison Break'
# query = 'Riverdale'
# query = 'Top Gear'
# query = 'Navy CIS'
# query = 'Money Heist'
# query = 'The 100'
# query = 'Game Of Thrones'
# query = 'The Witcher'
# query = 'Shadowhunters'
# query = 'Friends'
# query = 'The Office'
# query = 'The Last Airbender'
# query = 'Legends of Korra'
# query = 'Arcane'
# query = 'Pokemon'

# def load_page(url):
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument('--headless')
#     chrome_options.add_argument('window-size=1920x1080')
#     driver = webdriver.Chrome(options=chrome_options)
#     driver.get(url)
#     html = driver.page_source
#     driver.close()
#     return html


# def req(url: str):
#     page = load_page(url)
#     tree = html.fromstring(page)
#     return tree
#
#
# def retry_xpaths(url, xpath, retries=RETRIES):
#     for i in range(retries):
#         try:
#             tree = req(url)
#             result = tree.xpath(xpath)
#             elem = result[0]
#             return elem
#         except IndexError:
#             print(f'retrying {i + 1}/{retries}')
#             continue


# def find_imdb_page(search: str):
#     return retry_xpaths(url=f'{base_imdb_url}/find?q={search}',
#                         xpath='''//*[@id='__next']/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[1]/div[2]/div[1]/a''')
#
#
#
# pid = find_imdb_page(query)
# pid = pid.attrib['href']
# pid = pid.split('/')[2]
#
# print(f'''Found imdb page for search query '{query}' with page id '{pid}''')
#
# print('Loading number of seasons...')
#
# seasons = retry_xpaths(url=f'https://www.imdb.com/title/{pid}/episodes?season=1',
#                        xpath='''//*[@id='bySeason']''')
# num_seasons = len(seasons.value_options)
#
# print(f'Found {num_seasons} seasons')
#
# df = pd.DataFrame()
# for seas in range(1, num_seasons + 1):
#     retriesLeft = RETRIES
#     while retriesLeft > 0:
#         print(f'Loading Season {seas}/{num_seasons} ... (attempt {RETRIES - retriesLeft + 1}/{RETRIES})')
#         retriesLeft -= 1
#         tree = req(f'https://www.imdb.com/title/{pid}/episodes?season={seas}')
#         ep = 1
#         try:
#             for ep in range(1, MAX_EPISODES_TRY):
#                 xpath_loc = f'''//*[@id='episodes_content']/div[2]/div[2]/div[{ep}]/div[2]/div[2]/div[1]/span[2]'''
#                 rating_elem = tree.xpath(xpath_loc)
#                 rating = float(rating_elem[0].text)
#                 print(f'Episode {ep}: {rating:.1f}')
#                 df_ep = pd.DataFrame([{
#                     'season': seas,
#                     'episode': ep,
#                     'rating': rating
#                 }])
#                 df = pd.concat([df, df_ep], ignore_index=True)
#             print('Succesfully reached end of maximum of episodes to try')
#             break
#         except IndexError:
#             # dont retry if any episode found
#             if ep != 1:
#                 break
#
# print(f'Imported {num_seasons} seasons with a total of {len(df.index)} episodes')
#
# # remove whitespaces from file names
# fn = query.replace(" ", "_")
# df.to_csv(f'data/{fn}.csv', index=False)
