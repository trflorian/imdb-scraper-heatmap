from typing import List

import pandas as pd

from .models import Episode


def episodes_to_df(episodes: List[Episode]) -> pd.DataFrame:
    df = pd.DataFrame()
    for ep in episodes:
        df = pd.concat([df, pd.DataFrame([{
            'season': ep.season_num,
            'episode': ep.episode_num,
            'name': ep.name,
            'rating': ep.rating
        }])], ignore_index=True)
    return df


def df_to_episodes(df: pd.DataFrame) -> List[Episode]:
    episodes = []
    for _, row in df.iterrows():
        # indexing in df starts at 1, convert to 0-indexing
        sid = int(row['season'])-1
        eid = int(row['episode'])-1
        episodes.append(Episode(
            season_num=sid,
            episode_num=eid,
            name=row['name'],
            rating=row['rating'],
        ))
    return episodes
