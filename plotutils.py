import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional  # noqa

g_flushes = None  # type: Optional[pd.DataFrame]


def set_flushes(val: pd.DataFrame):
    global g_flushes
    g_flushes = val


def overlay_flushes(flushes):
    for t in flushes:
        plt.axvline(x=t, color='k', linestyle=':')


def plot(df, title=None, secondary_y=[], ylabel='', ylabel2=''):
    """Generate a plot from a datafame, with flushes overlaid."""
    plt.figure()
    ax = df.plot(title=title, secondary_y=secondary_y)
    if ylabel:
        ax.set_ylabel(ylabel)
    if ylabel2:
        ax.right_ax.set_ylabel(ylabel2)
    if g_flushes is not None:
        overlay_flushes(g_flushes.index)


def strip_suffix(label: str) -> str:
    return label.split(':')[0]


def select(df: pd.DataFrame, suffix: str):
    frame = df[[c for c in df.columns if c.endswith(':' + suffix)]]
    return frame.rename(strip_suffix, axis='columns')
