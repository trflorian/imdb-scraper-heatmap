import time

from lxml import html
from dataclasses import dataclass

import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

@dataclass
class ImdbEntry:
    id: str
    title: str
    year: int
    type: str

@dataclass
class Episode:
    name: str
    season_num: int
    episode_num: int
    rating: float

class ImdbScraper:
    timeout = 1
    max_retries = 10
    max_episodes = 100
    base_url = 'https://www.imdb.com'
    driver = None
    variant = None

    xpaths = {
        'result_list': [
            '''//*[@id='__next']/main/div[2]/div[3]/section/div/div[1]/section[3]/div[2]/ul''',
            '//*[@id="main"]/div/div[2]/table/tbody'
        ],
        'entry_id': [
            '//*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[{}]/div[2]/div[1]/a',
            '//*[@id="main"]/div/div[2]/table/tbody/tr[{}]/td[2]/a'
        ],
        'entry_year': [
            '//*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[{}]/div[2]/div[1]/ul[1]/li[1]/label',
            '//*[@id="main"]/div/div[2]/table/tbody/tr[{}]/td[2]'
        ],
        'num_seasons': [
            '''//*[@id='bySeason']'''
        ]
    }

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
        self.page_loaded = False
        self.driver.close()
        self.driver = webdriver.Chrome(options=self.chrome_options)

    def _load_url(self, imdb_url: str):
        self.variant = None
        print(f'Fetching from {imdb_url}')
        self.driver.implicitly_wait(1)
        self.driver.get(f'{self.base_url}/{imdb_url}')

    def _load_element(self, xpaths):
        if self.variant is None:
            try:
                element_present = EC.presence_of_element_located((By.XPATH, xpaths[0]))
                WebDriverWait(self.driver, timeout=self.timeout).until(element_present)
                self.variant = 0
            except TimeoutException:
                self.variant = min(1, len(xpaths)-1)

            print(f'Loaded variant {self.variant}')

        # prefer to use variant indexed xpath, but check others if no match
        xp_var = xpaths[self.variant]
        prioritized_xpaths = [xp_var, *[xp for xp in xpaths if xp != xp_var]]

        for xp in prioritized_xpaths:
            tree = html.fromstring(self.driver.page_source)
            matches = tree.xpath(xp)
            if len(matches) == 0:
                continue
            self.variant = xpaths.index(xp)
            return matches[0]

        return None

    def _find_element_initial(self, imdb_url: str, xpaths):
        for attempt in range(self.max_retries):
            print(f'find_element attempt ({attempt+1}/{self.max_retries})')
            self._load_url(imdb_url)
            elem = self._load_element(xpaths)
            if elem is None:
                self._restart_driver()
                continue
            return elem
        print('Failed to find xpath element.')
        return None

    def _xpf(self, xpid, arg):
        return [p.format(arg) for p in self.xpaths[xpid]]

    def search(self, search_text: str, search_type: str = None):
        results = []

        # [None, 'tv', 'ft']
        type_query = ''
        if search_type is not None:
            type_query = f'&s=tt&type={search_type}'

        search_text = search_text.replace(' ', '%20')

        search_results = self._find_element_initial(
            imdb_url=f'/find?q={search_text}{type_query}',
            xpaths=self.xpaths['result_list']
        )

        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul --- if matches, ul children <= 5
        num_results = len(search_results)

        # individual results
        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[1]/div[2]/div[1]/a
        # //*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[2]/div[2]/div[1]/a
        # xpath=f'//*[@id="__next"]/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[{li_index}]/div[2]/div[1]/a'

        for i in range(num_results):
            li_index = i+1

            # extract href from <a> tag
            id_elem = self._load_element(
                xpaths=self._xpf('entry_id', li_index)
            )
            entry_name = id_elem.text

            entry_id = id_elem.attrib['href'].split('/')[2]

            year_elem = self._load_element(
                xpaths=self._xpf('entry_year', li_index)
            )

            if self.variant == 0:
                year_text = year_elem.text
                year_splits = year_text.replace(' ', '').split('–')
                entry_type = 'ft' if len(year_splits) == 1 else 'tv'
                entry_year = int(year_splits[0])
            else:
                info_text = year_elem[0].tail.replace(' ', '')
                infos = info_text.split('(')
                entry_year = infos[1][:infos[1].index(')')]
                entry_type = infos[2][:infos[2].index(')')]
                entry_type = 'tv' if entry_type == 'TVSeries' else 'ft'

            if search_type is not None and search_type != entry_type:
                print(f'WARNING: found an entry of type {entry_type} but search query was for type {search_type}')

            results.append(ImdbEntry(
                id=entry_id,
                title=entry_name,
                year=entry_year,
                type=entry_type
            ))

        return results

    def get_all_episodes(self, series_id: str):
        episodes = []

        seasons_dropdown = self._find_element_initial(
            imdb_url=f'/title/{series_id}/episodes?season=1',
            xpaths=self.xpaths['num_seasons']
        )

        num_seasons = 0
        for seas_num, val in enumerate(seasons_dropdown.value_options):
            if str(seas_num + 1) == val:
                num_seasons += 1

        print(f'Found {num_seasons} seasons')

        for i in range(num_seasons):
            season_num = i + 1
            episodes.append(self.get_episodes(series_id, season_num))

        return episodes

    def get_episodes(self, series_id: str, season_num: int):
        episodes = []

        self._find_element_initial(
            imdb_url=f'/title/{series_id}/episodes?season={season_num}',
            xpaths=[f'''//*[@id='episodes_content']/div[2]/div[2]/div[{1}]/div[2]/div[2]/div[1]/span[2]''']
        )

        ep = 0
        try:
            for ep in range(0, self.max_episodes):
                episode_num = ep+1

                rating_elem = self._load_element(
                    xpaths=[f'''//*[@id='episodes_content']/div[2]/div[2]/div[{episode_num}]/div[2]/div[2]/div[1]/span[2]''']
                )
                if rating_elem is None:
                    break
                rating = float(rating_elem.text)
                print(f'Ep {episode_num} is rated {rating}')
                episodes.append(Episode(
                    season_num=season_num,
                    episode_num=episode_num,
                    name=f'Episode {episode_num}',
                    rating=rating,
                ))
        except IndexError:
            pass
        print(f'Found {ep} episodes in season {season_num}')

        return episodes

query = 'Breaking Bad'
with ImdbScraper() as sc:
    entry = sc.search(search_text=query, search_type=None)[0]
    eid = entry.id
    episodes = sc.get_all_episodes(eid)
    print(episodes)


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
