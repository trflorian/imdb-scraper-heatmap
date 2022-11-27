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
        episodes.append(Episode(
            season_num=int(row['season']),
            episode_num=int(row['episode']),
            name=row['name'],
            rating=row['rating'],
        ))
    return episodes
