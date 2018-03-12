#!/usr/bin/python3

import argparse
import os
import datetime
import webbrowser

import matplotlib
matplotlib.use('cairo')

import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
import numpy as np

from typing import Dict, List

import unpack


def configure_matplotlib(dpi=200, figsize=(8, 6)):
    matplotlib.rcParams['figure.dpi'] = dpi
    matplotlib.rcParams['figure.figsize'] = figsize


def sec_formatter(t, _):
    dt = datetime.timedelta(seconds=int(t))
    return str(dt)


def fmt_commit(hostinfo: Dict[str, str]) -> str:
    return '{}:{}'.format(hostinfo['git:branch'], hostinfo['git:commit'][:8])


def pd_to_np(data) -> np.ndarray:
    vec = np.array([data.index, data])
    vec[np.isnan(vec)] = 0.
    return vec


def get_progress(df):
    updatetip = df['frames']['updatetip']
    try:
        return pd_to_np(updatetip['progress'] * 100)
    except KeyError:
        return pd_to_np(updatetip['pct'])


def make_figure(data1,
                data2,
                outname: str,
                labels: List[str],
                hours_per_tick: int = 2):
    a = get_progress(data1)
    b = get_progress(data2)

    # Trim the time axis.
    maxta = a[0].max()
    maxtb = b[0].max()
    maxt = min(maxta, maxtb)
    if maxta > maxt:
        ix = np.argmax(a[0] > maxt)
        a = a[:, :ix]
    if maxtb > maxt:
        ix = np.argmax(b[0] > maxt)
        b = b[:, :ix]

    ax = plt.axes()
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Progress', fontsize=12)
    ax.set_title('Bitcoin Initial Block Download (IBD)', fontsize=14)

    plt.plot(a[0], a[1], 'r', b[0], b[1], 'b')

    # round up to the next hour
    hours = (maxt // 3600) + 1
    maxt = hours * 3600
    ax.set_xlim(-1800, maxt)

    maxtick = 0
    ticks = [maxtick]
    while True:
        maxtick += 3600 * hours_per_tick
        if maxtick <= maxt:
            ticks.append(maxtick)
        else:
            break
    ax.set_xticks(ticks)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(sec_formatter))

    plt.legend(labels=labels)
    plt.savefig(outname)


def load_file(name: str):
    try:
        return unpack.unpack_data_strict(name)
    except FileNotFoundError:
        return unpack.unpack_data(name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', default='out.png', help='Output filename')
    parser.add_argument('-t', '--hours-per-tick', default=1, type=int)
    parser.add_argument('--labels', default='', help='Label 1')
    parser.add_argument('log1')
    parser.add_argument('log2')
    args = parser.parse_args()

    df1 = load_file(args.log1)
    df2 = load_file(args.log2)

    if args.labels:
        labels = [l.strip() for l in args.labels.split(',')]
        assert len(labels) == 2
    else:
        labels = [fmt_commit(df1['hostinfo']), fmt_commit(df2['hostinfo'])]

    configure_matplotlib()
    make_figure(df1, df2, args.output, labels, args.hours_per_tick)

    abs_dest = os.path.abspath(args.output)
    try:
        browser = webbrowser.get('firefox')
        browser.open('file://' + abs_dest)
    except webbrowser.Error:
        print(abs_dest)


if __name__ == '__main__':
    main()
