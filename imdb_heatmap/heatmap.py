from typing import List

import numpy as np

import matplotlib
import matplotlib.pyplot as plt

from .models import Episode
from .serializer import episodes_to_df

def create_heatmap(episodes: list[Episode]) -> np.ndarray:
    # read ratings for series
    df = episodes_to_df(episodes)

    # extract dimension of series
    seasons = df['season'].max()
    episodes = df['episode'].max()

    # initialize heatmap with zeros
    heatmap = np.zeros([seasons, episodes])

    for _, row in df.iterrows():
        # indexing in df starts at 1, convert to 0-indexing
        sid = int(row['season'])-1
        eid = int(row['episode'])-1
        rating = row['rating']

        # write rating in heatmap
        heatmap[seasons - sid - 1, eid] = rating

    # maks out unused squares
    heatmap = np.ma.masked_where(heatmap == 0.0, heatmap)

    return heatmap

def heatmap_plot(series_name: str, episodes: List[Episode], show: bool, save_fn: str or None,
                 dark_mode: bool, dark_col=(0.16, 0.16, 0.16, 1.0)) -> None:
    # create the heatmap array
    heatmap = create_heatmap(episodes)

    # TODO
    matplotlib.use('TkAgg')

    # scale figure appropriately
    figsize = np.array(heatmap.shape[::-1])
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

    # plot heatmap and inner ratings text
    plt.imshow(heatmap)
    for sid in range(heatmap.shape[0]):
        for eid in range(heatmap.shape[1]):
            rating = heatmap[sid, eid]
            plt.text(eid, sid, f'{rating}', ha='center', va='center', color='w', fontsize=7)

    # format tick labels
    ticks = [np.arange(heatmap.shape[i]) for i in [0, 1]]
    plt.yticks(ticks[0][::-1], labels=[f'{i+1}' for i in ticks[0]])
    plt.xticks(ticks[1], labels=[f'{i+1}' for i in ticks[1]])

    # format axis labels
    plt.xlabel('Episode')
    plt.ylabel('Season')

    # title with whitespaces
    title = series_name.replace('_', ' ')
    plt.title(title)

    # plot heatmap
    plt.tight_layout()

    # optionally save or display the plot
    if save_fn is not None:
        if dark_mode:
            plt.savefig(save_fn, facecolor=dark_col)
        else:
            plt.savefig(save_fn)
    if show:
        plt.show()