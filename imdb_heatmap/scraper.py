from typing import List

from lxml import html

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .models import Episode, ImdbEntry

class ImdbScraper:
    timeout = 10
    max_retries = 20
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

    def _restart_driver(self) -> None:
        self.page_loaded = False
        self.driver.delete_all_cookies()
        self.driver.close()
        self.driver = webdriver.Chrome(options=self.chrome_options)

    def _load_url(self, imdb_url: str) -> None:
        self.variant = None
        print(f'Fetching from {imdb_url}')
        #self.driver.implicitly_wait(1)
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

    def _xpf(self, xpid, arg) -> List[str]:
        return [p.format(arg) for p in self.xpaths[xpid]]

    def search(self, search_text: str, search_type: str = None, max_results: int = 5) -> List[ImdbEntry]:
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

        # cap results at max_results
        num_results = min(max_results, num_results)

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
                if year_elem is None:
                    entry_year = 0
                    entry_type = 'na'
                else:
                    year_splits = year_text.replace(' ', '').split('–')
                    entry_type = 'ft' if len(year_splits) == 1 else 'tv'
                    entry_year = int(year_splits[0])
            else:
                info_text = year_elem[0].tail.replace(' ', '')
                infos = info_text.split('(')
                if len(infos) == 1:
                    entry_year = 0
                    entry_type = 'na'
                else:
                    entry_year = infos[1][:infos[1].index(')')]
                    if len(infos) == 2:
                        entry_type = 'ft'
                    else:
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

    def get_all_episodes(self, series_id: str) -> List[Episode]:
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
            episodes.extend(self.get_episodes(series_id, season_num))

        return episodes

    def get_episodes(self, series_id: str, season_num: int) -> List[Episode]:
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

                name_elem = self._load_element(
                    xpaths=[f'//*[@id="episodes_content"]/div[2]/div[2]/div[{episode_num}]/div[2]/strong/a']
                )
                ep_name = name_elem.text

                print(f'S{season_num} E{episode_num} rating={rating:.1f} name="{ep_name}"')
                episodes.append(Episode(
                    season_num=season_num,
                    episode_num=episode_num,
                    name=ep_name,
                    rating=rating,
                ))
        except IndexError:
            pass
        print(f'Found {ep} episodes in season {season_num}')

        return episodes
