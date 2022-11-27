from dataclasses import dataclass


@dataclass
class ImdbEntry:
    id: str
    title: str
    year: int
    type: str

@dataclass
class Episode:
    name: str
    season_num: int
    episode_num: int
    rating: float
