import os

import argparse

from tqdm import tqdm

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

dark_col = (0.16, 0.16, 0.16, 1.0)

def img_path(series: str) -> str:
    return f'heatmaps/{series}.png'

def heatmap_plot(series: str, show: bool, save: bool, dark_mode: bool) -> None:

    # read ratings for series
    df = pd.read_csv(f'data/{series}.csv')

    # extract dimension of series
    seasons = df['season'].max()
    episodes = df['episode'].max()

    # initialize heatmap with zeros
    heatmap = np.zeros([seasons, episodes])

    # scale figure appropriately
    figsize = np.array([episodes, seasons])
    figsize = figsize/3
    minax = np.min(figsize)
    minsize = 2.3
    if minax < minsize:
        figsize = figsize / minax * minsize
    plt.figure(figsize=figsize, dpi=200)

    # dark mode
    if dark_mode:
        plt.style.use("dark_background")
        plt.gca().set_facecolor(dark_col)
        plt.gcf().set_facecolor(dark_col)

    for _, row in df.iterrows():
        # indexing in df starts at 1, convert to 0-indexing
        sid = int(row['season'])-1
        eid = int(row['episode'])-1
        rating = row['rating']

        # write rating in heatmap
        heatmap[seasons - sid - 1, eid] = rating

        # add rating text
        plt.text(eid, seasons - sid - 1, f'{rating}', ha='center', va='center', color='w', fontsize=7)

    # maks out unused squares
    heatmap = np.ma.masked_where(heatmap < 0.1, heatmap)

    # format tick labels
    ticks = [np.arange(heatmap.shape[i]) for i in [0, 1]]
    plt.yticks(ticks[0][::-1], labels=[f'{i+1}' for i in ticks[0]])
    plt.xticks(ticks[1], labels=[f'{i+1}' for i in ticks[1]])

    # format axis labels
    plt.xlabel('Episode')
    plt.ylabel('Season')

    # title with whitespaces
    title = series.replace('_', ' ')
    plt.title(title)

    # plot heatmap
    plt.tight_layout()
    plt.imshow(heatmap)

    # optionally save or display the plot
    fn = img_path(series)
    if save:
        if dark_mode:
            plt.savefig(fn, facecolor=dark_col)
        else:
            plt.savefig(fn)
    if show:
        plt.show()

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

    # if custom series name supplied from arguments, use this. otherwise load all series from data directory
    if custom_series is not None:
        all_series = [custom_series]
    else:
        # load all series in data folder
        all_series = ['.'.join(s.split('.')[:-1]) for s in os.listdir('data')]

    # check override
    if len(all_series) > 0 and save and not override:
        tot_before = len(all_series)
        all_series = [s for s in all_series if not os.path.isfile(img_path(s))]
        tot_after = len(all_series)
        if tot_after < tot_before:
            print(f'Ignoring {tot_before - tot_after}/{tot_before} series because these heatmap images already exist '
                  f'and override flag is not set.')

    # create heatmap plots
    if len(all_series) == 0:
        print('No series to plot...')
    else:
        for series in tqdm(all_series):
            heatmap_plot(series, show=show, save=save, dark_mode=dark_mode)

if __name__ == '__main__':
    main()
