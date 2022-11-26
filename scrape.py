from selenium import webdriver
from lxml import html

import pandas as pd

# config
RETRIES = 3
MAX_EPISODES_TRY = 30

base_imdb_url = 'https://www.imdb.com'

# Movie/Series to search for
# query = 'Breaking Bad'
# query = 'Dark'
# query = 'Prison Break'
# query = 'Riverdale'
# query = 'Top Gear'
# query = 'Navy CIS'
# query = 'Money Heist'
query = 'The 100'


def load_page(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    html = driver.page_source
    driver.close()
    return html


def req(url: str):
    page = load_page(url)
    tree = html.fromstring(page)
    return tree


def retry_xpaths(url, xpath, retries=RETRIES):
    for i in range(retries):
        try:
            tree = req(url)
            result = tree.xpath(xpath)
            elem = result[0]
            return elem
        except:
            print(f'retrying {i + 1}/{retries}')
            continue


def find_imdb_page(search: str):
    return retry_xpaths(url=f'{base_imdb_url}/find?q={search}',
                        xpath='''//*[@id='__next']/main/div[2]/div[3]/section/div/div[1]/section[2]/div[2]/ul/li[1]/div[2]/div[1]/a''')


pid = find_imdb_page(query)
pid = pid.attrib['href']
pid = pid.split('/')[2]

print(f'''Found imdb page for search query '{query}' with page id '{pid}''')

print('Loading seasons cnt...')

seasons = retry_xpaths(url=f'https://www.imdb.com/title/{pid}/episodes?season=1',
                       xpath='''//*[@id='bySeason']''')
num_seasons = len(seasons.value_options)

print(f'Found {num_seasons} seasons')

df = pd.DataFrame()
for seas in range(1, num_seasons + 1):
    retriesLeft = RETRIES
    while retriesLeft > 0:
        print(f'Loading Season {seas} ({RETRIES - retriesLeft + 1}/{RETRIES})...')
        retriesLeft -= 1
        tree = req(f'https://www.imdb.com/title/{pid}/episodes?season={seas}')
        for ep in range(1, MAX_EPISODES_TRY):
            xpath_loc = f'''//*[@id='episodes_content']/div[2]/div[2]/div[{ep}]/div[2]/div[2]/div[1]/span[2]'''
            rating_elem = tree.xpath(xpath_loc)
            try:
                rating = float(rating_elem[0].text)
                print(f'Episode {ep} : {rating:.1f}')
                df_ep = pd.DataFrame([{
                    'season': seas,
                    'episode': ep,
                    'rating': rating
                }])
                df = pd.concat([df, df_ep], ignore_index=True)
            except:
                # retry if no episodes found
                if ep != 1:
                    retriesLeft = 0
                break

print(f'Imported {num_seasons} seasons with a total of {len(df.index)} episodes')
df.to_csv(f'data/{query}.csv', index=False)
