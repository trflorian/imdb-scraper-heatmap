from imdb_heatmap.scraper import ImdbScraper
from imdb_heatmap.serializer import episodes_to_df

import pandas as pd

def main():

    # Movie/Series to search for
    # query = 'Breaking Bad'
    query = 'Dark'
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

    with ImdbScraper() as sc:
        imdb_entry = sc.search(search_text=query, search_type=None)[0]
        title = imdb_entry.title
        if imdb_entry.type != 'tv':
            print(f'Found imdb entry {title} is not a series.')
            return
        episodes = sc.get_all_episodes(imdb_entry.id)

    df = episodes_to_df(episodes)

    fn = query.replace(' ', '_')
    df.to_csv(f'examples/data/{fn}.csv', index=False)

if __name__ == '__main__':
    main()