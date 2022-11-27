import argparse
import os

import pandas as pd
from tqdm import tqdm

from imdb_heatmap.heatmap import heatmap_plot
from imdb_heatmap.serializer import df_to_episodes


def to_fn(series: str) -> str:
    return series.replace(' ', '_')

def fn_match(f1: str, f2: str):
    f1 = f1.lower().replace(' ', '').replace('_', '').replace(':', '')
    f2 = f2.lower().replace(' ', '').replace('_', '').replace(':', '')
    return f1 in f2 or f2 in f1

def main():
    # define and parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--show', action='store_true', help='show the heatmap plot instead of saving it')
    parser.add_argument('-d', '--dark', action='store_true', help='use dark mode for the plot style')
    parser.add_argument('-o', '--override', action='store_true', help='override existing plots')
    parser.add_argument('-n', '--name', type=str, default=None,
                        help='name of the series, if not set the whole data directory will be scanned')
    args = parser.parse_args()

    # config from args
    show = args.show
    save = not show
    override = args.override
    dark_mode = args.dark
    custom_series = args.name

    # paths
    img_path = 'examples/img'
    data_path = 'examples/data'

    # if custom series name supplied from arguments, use this. otherwise load all series from data directory
    all_series = ['.'.join(s.split('.')[:-1]) for s in os.listdir('examples/data')]
    if custom_series is not None:
        series = [custom_series]
    else:
        # load all series in data folder
        series = all_series

    # create heatmap plots
    if len(series) == 0:
        print('No series to plot...')
    else:
        for s in tqdm(series):
            fn_s = to_fn(s)
            fn_data = f'{data_path}/{fn_s}.csv'
            if not os.path.isfile(fn_data):
                # try to find closest match
                matches = [m for m in all_series if fn_match(s, m)]
                if len(matches) == 0:
                    print(f'No match found in data for {s}.')
                    continue
                fn_data = f'{data_path}/{to_fn(matches[0])}.csv'
                fn_s = matches[0]
            df = pd.read_csv(fn_data)
            episodes = df_to_episodes(df)

            # don't override file if already exists and flag is not set
            save_fn = f'{img_path}/{fn_s}.png'
            if os.path.isfile(save_fn) and not override:
                save_fn = None

            heatmap_plot(series_name=s, episodes=episodes, show=show, save_fn=save_fn,
                         dark_mode=dark_mode, dpi=150)

if __name__ == '__main__':
    main()
