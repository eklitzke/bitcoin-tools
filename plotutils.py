import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional  # noqa

flushes = None  # type: Optional[pd.DataFrame]


def set_flushes(val: pd.DataFrame):
    global flushes
    flushes = val


def plot(df, title=None, secondary_y=[], ylabel='', ylabel2=''):
    """Generate a plot from a datafame, with flushes overlaid."""
    plt.figure()
    ax = df.plot(title=title, secondary_y=secondary_y)
    if ylabel:
        ax.set_ylabel(ylabel)
    if ylabel2:
        ax.right_ax.set_ylabel(ylabel2)
    for t in flushes.index:
        plt.axvline(x=t, color='k', linestyle=':')


def strip_suffix(label: str) -> str:
    return label.split(':')[0]


def select(df: pd.DataFrame, suffix: str):
    frame = df[[c for c in df.columns if c.endswith(':' + suffix)]]
    return frame.rename(strip_suffix, axis='columns')
