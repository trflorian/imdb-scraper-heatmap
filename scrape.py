from .scraper.scraper import ImdbScraper

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
        entry = sc.search(search_text=query, search_type=None)[0]
        eid = entry.id
        episodes = sc.get_all_episodes(eid)
        print(episodes)

    df = pd.DataFrame()
    for ep in episodes:
        df = pd.concat([df, pd.DataFrame([{
            'season': ep.season_num,
            'episode': ep.episode_num,
            'name': ep.name,
            'rating': ep.rating
        }])], ignore_index=True)

    fn = query.replace(' ', '_')
    df.to_csv(f'data/{fn}.csv', index=False)

if __name__ == '__main__':
    main()