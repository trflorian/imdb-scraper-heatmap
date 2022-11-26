import os

from tqdm import tqdm

import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

def heatmap_plot(series: str, show=True, save=True):
    df = pd.read_csv(f'data/{series}.csv')

    seasons = df['season'].max()
    episodes = df['episode'].max()

    heatmap = np.zeros([seasons, episodes])

    # ratio = seasons/episodes
    # avg_size = np.max([seasons, episodes])
    # initial_size = avg_size / 8
    # figsize = np.array([initial_size, initial_size*ratio])
    # if ratio < 1:
    #     figsize /= ratio
    # min_size = np.min(figsize)
    # if min_size < 3.5:
    #     figsize *= 3.5/min_size
    figsize = np.array([episodes, seasons])
    figsize = figsize/3
    minax = np.min(figsize)
    minsize = 2.3
    if minax < minsize:
        figsize = figsize / minax * minsize
    plt.figure(figsize=figsize, dpi=200)

    for _, row in df.iterrows():
        sid = int(row['season'])-1
        eid = int(row['episode'])-1
        rating = row['rating']
        heatmap[seasons - sid - 1, eid] = rating
        plt.text(eid, seasons - sid - 1, f'{rating}', ha='center', va='center', color='w', fontsize=7)

    heatmap = np.ma.masked_where(heatmap < 0.1, heatmap)

    ticks = [np.arange(heatmap.shape[i]) for i in [0, 1]]
    plt.yticks(ticks[0][::-1], labels=[f'{i+1}' for i in ticks[0]])
    plt.xticks(ticks[1], labels=[f'{i+1}' for i in ticks[1]])

    plt.xlabel('Episode')
    plt.ylabel('Season')

    plt.title(series)
    plt.imshow(heatmap)
    plt.tight_layout()
    if save:
        plt.savefig(f'heatmaps/{series}.png')
    if show:
        plt.show()

def main():
    all_series = os.listdir('data')
    all_series = ['.'.join(s.split('.')[:-1]) for s in all_series]
    for series in tqdm(all_series):
        heatmap_plot(series, show=False, save=True)

if __name__ == '__main__':
    main()
