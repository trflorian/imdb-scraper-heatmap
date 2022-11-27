import os
import argparse

from imdb_heatmap.scraper import ImdbScraper
from imdb_heatmap.serializer import episodes_to_df

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
                queries.append(line)

    if len(queries) == 0:
        print('No query supplied. Use --help to see how to usae this command.')
    else:
        for query in queries:
            with ImdbScraper() as sc:
                imdb_entry = sc.search(search_text=query, search_type=None)[0]
                title = imdb_entry.title
                if imdb_entry.type != 'tv':
                    print(f'Found imdb entry {title} is not a series.')
                    return
                episodes = sc.get_all_episodes(imdb_entry.id)

            df = episodes_to_df(episodes)

            fn = title.replace(' ', '_')
            df.to_csv(f'examples/data/{fn}.csv', index=False)

if __name__ == '__main__':
    main()
