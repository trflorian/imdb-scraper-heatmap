import os
import argparse

from seriesheatmap.scraper import ImdbScraper
from seriesheatmap.serializer import episodes_to_df

def main():
    # define and parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', type=str, help='name of the series to scrape')
    parser.add_argument('-f', '--file', type=str, help='path to a file with a list of series to scrape')
    args = parser.parse_args()

    # extract query
    queries = []

    if args.name is not None:
        queries.append(args.name)

    if args.file is not None:
        if not os.path.isfile(args.file):
            raise ValueError('Supplied argument file does not exist')

        with open(args.file, 'r') as f:
            for line in f.readlines():
                # ignore empty or commented lines
                l_trimmed = line.replace(' ', '')
                if len(l_trimmed) > 0 and not l_trimmed.startswith('#'):
                    queries.append(line)

    if len(queries) == 0:
        print('No query supplied. Use --help to see how to usae this command.')
    else:
        print(f'Scraping {len(queries)} series')
        for query in queries:
            with ImdbScraper() as sc:
                entries = sc.search(search_text=query, search_type='tv', max_results=5)
                series_entries = [e for e in entries if e.type == 'tv']
                if len(series_entries) == 0:
                    closest_match_text = ''
                    if len(entries) > 0:
                        e = entries[0]
                        closest_match_text = f'Closest match: id="{e.id}" name="{e.title}" type="{e.type}"'
                    print(f'Found no imdb entry for query "{query}". {closest_match_text}')
                    continue
                imdb_entry = series_entries[0]
                title = imdb_entry.title
                episodes = sc.get_all_episodes(imdb_entry.id)

            df = episodes_to_df(episodes)

            fn = title.replace(' ', '_').replace(':', '')
            df.to_csv(f'examples/data/{fn}.csv', index=False)

if __name__ == '__main__':
    main()
