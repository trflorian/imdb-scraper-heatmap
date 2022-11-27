import argparse
import os

import pandas as pd
from tqdm import tqdm

from imdb_heatmap.heatmap import heatmap_plot
from imdb_heatmap.serializer import df_to_episodes


def fn(series: str) -> str:
    return series.replace(' ', '_')

def main():
    # define and parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--show', action='store_true', help='show the heatmap plot instead of saving it')
    parser.add_argument('-d', '--dark', action='store_true', help='use dark mode for the plot style')
    parser.add_argument('-o', '--override', action='store_true', help='override existing plots, only used if show flag is not set')
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
    if custom_series is not None:
        all_series = [custom_series]
    else:
        # load all series in data folder
        all_series = ['.'.join(s.split('.')[:-1]) for s in os.listdir('../examples/data')]

    # check override
    if len(all_series) > 0 and save and not override:
        tot_before = len(all_series)
        all_series = [s for s in all_series if not os.path.isfile(f'{img_path}/{fn(s)}.png')]
        tot_after = len(all_series)
        if tot_after < tot_before:
            print(f'Ignoring {tot_before - tot_after}/{tot_before} series because these heatmap images already exist '
                  f'and override flag is not set.')

    # create heatmap plots
    if len(all_series) == 0:
        print('No series to plot...')
    else:
        for series in tqdm(all_series):
            df = pd.read_csv(f'{data_path}/{fn(series)}.csv')
            episodes = df_to_episodes(df)
            heatmap_plot(series_name=series, episodes=episodes, show=show, save_fn=f'{img_path}/{fn(series)}.png',
                         dark_mode=dark_mode)

if __name__ == '__main__':
    main()
