import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

from tqdm import tqdm

import numpy as np
import pandas as pd

# series = "Top Gear"
# series = "Bones"
# series = "Navy CIS"
# series = "Money Heist"
# series = "Dark"
# series = "Breaking Bad"

#all_series = ["Breaking Bad", "Dark", "Money Heist", "Navy CIS", "Bones", "Top Gear", "Prison Break", "Riverdale"]
all_series = ["The 100"]

def heatmap_plot(series: str, show=True, save=True):
    df = pd.read_csv(f"data/{series}.csv")

    seasons = df["season"].max()
    episodes = df["episode"].max()

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
        sid = int(row["season"])-1
        eid = int(row["episode"])-1
        rating = row["rating"]
        heatmap[seasons - sid - 1, eid] = rating
        plt.text(eid, seasons - sid - 1, f"{rating}", ha="center", va="center", color="w", fontsize=7)

    heatmap = np.ma.masked_where(heatmap < 0.1, heatmap)

    ticks = [np.arange(heatmap.shape[i]) for i in [0, 1]]
    plt.yticks(ticks[0][::-1], labels=[f"{i+1}" for i in ticks[0]])
    plt.xticks(ticks[1], labels=[f"{i+1}" for i in ticks[1]])

    plt.xlabel("Episode")
    plt.ylabel("Season")

    plt.title(series)
    plt.imshow(heatmap)
    plt.tight_layout()
    if save:
        plt.savefig(f"heatmaps/{series}.png")
    if show:
        plt.show()

for series in tqdm(all_series):
    heatmap_plot(series, show=True, save=True)