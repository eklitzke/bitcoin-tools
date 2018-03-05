#!/usr/bin/python3

import argparse

import datetime
import matplotlib
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm

from typing import Any, Dict, Tuple

import unpack


def configure_matplotlib(dpi=300, figsize=(12, 8)):
    matplotlib.rcParams['figure.dpi'] = dpi
    matplotlib.rcParams['figure.figsize'] = figsize


def sec_formatter(t, _):
    dt = datetime.timedelta(seconds=t)
    return str(dt)


def create_dataframe(core: Dict[str, Any], leveldb: Dict[str, Any]
                     ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    c_commit = core['hostinfo']['git:commit'][:8]

    l_commit = leveldb['hostinfo']['git:commit'][:8]

    c = core['frames']['updatetip']['progress']
    l = leveldb['frames']['updatetip']['progress']

    def rel_ctime(t):
        return t - c.index[0]

    def rel_ltime(t):
        return t - l.index[0]

    cx = 0
    lx = 0

    times = []
    cvals = []
    lvals = []
    while cx < len(c) or lx < len(l):
        if cx >= len(c):
            times.append(rel_ltime(l.index[lx]))
            cvals.append(None)
            lvals.append(l[lx])
            lx += 1
            continue
        elif lx >= len(l):
            times.append(rel_ctime(c.index[cx]))
            cvals.append(c[cx])
            lvals.append(None)
            cx += 1
            continue

        ct = rel_ctime(c.index[cx])
        cv = c[cx]

        lt = rel_ltime(l.index[lx])
        lv = l[lx]

        if ct == lt:
            times.append(ct)
            cvals.append(cv)
            cx += 1
            lvals.append(lv)
            lx += 1
        elif ct < lt:
            times.append(ct)
            cvals.append(cv)
            cx += 1
            lv = lvals[-1] if lvals else None
            lvals.append(lv)
        else:
            assert lt < ct
            times.append(lt)
            lvals.append(lv)
            lx += 1
            cv = cvals[-1] if cvals else None
            cvals.append(cv)

    assert len(cvals) == len(lvals) == len(times)

    times = np.array(
        [t.to_timedelta64() / 1e9 for t in times], dtype=np.float64)

    c_flushes = list(core['frames']['flushes'].index - c.index[0])
    l_flushes = list(leveldb['frames']['flushes'].index - l.index[0])

    c_flushes = np.array(
        [t.to_timedelta64() / 1e9 for t in c_flushes], dtype=np.float64)
    l_flushes = np.array(
        [t.to_timedelta64() / 1e9 for t in l_flushes], dtype=np.float64)

    return pd.DataFrame(
        {
            'master ' + c_commit: cvals,
            'eklitzke ' + l_commit: lvals,
            't': times,
        },
        index=times), c_flushes, l_flushes


def make_figure(df: pd.DataFrame, c_flushes: np.ndarray, l_flushes: np.ndarray,
                outname: str):
    columns = list(sorted(c for c in df.columns if c != 't'))
    cmap = cm.get_cmap('coolwarm')
    ax = (df[columns] * 100).plot(colormap=cmap)
    ax.set_xlabel('Time')
    ax.set_ylabel('Progress')
    ax.set_title('Bitcoin IBD Progress')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(sec_formatter))

    for x in l_flushes:
        plt.axvline(x=x, color=cmap(0.0), linestyle=':')

    for x in c_flushes:
        plt.axvline(x=x, color=cmap(1.0), linestyle=':')

    plt.savefig(outname)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', default='out.png', help='Output filename')
    args = parser.parse_args()

    configure_matplotlib()

    core = unpack.unpack_data('bitcoin-core')
    leveldb = unpack.unpack_data('leveldb')

    df, c_flushes, l_flushes = create_dataframe(core, leveldb)
    make_figure(df, c_flushes, l_flushes, args.output)


if __name__ == '__main__':
    main()
