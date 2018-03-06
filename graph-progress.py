#!/usr/bin/python3

import argparse
import os
import datetime
import webbrowser

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


def fmt_commit(hostinfo: Dict[str, str]) -> str:
    return '{}:{}'.format(hostinfo['git:branch'], hostinfo['git:commit'][:8])


def make_figure(data1, data2, outname: str):
    cmap = cm.get_cmap('coolwarm')
    prog1 = data1['frames']['updatetip']['progress'] * 100
    prog2 = data2['frames']['updatetip']['progress'] * 100
    prog1.plot()
    prog2.plot()
    plt.legend(
        labels=[fmt_commit(data1['hostinfo']),
                fmt_commit(data2['hostinfo'])])

    ax = plt.axes()
    ax.set_xlabel('Time')
    ax.set_ylabel('Progress')
    ax.set_title('Bitcoin IBD Progress')
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(sec_formatter))

    if False:
        flushes1 = data1['frames']['flushes']
        flushes2 = data1['frames']['flushes']
        for x in flushes1:
            plt.axvline(x=x, color=cmap(0.0), linestyle=':')

        for x in flushes2:
            plt.axvline(x=x, color=cmap(1.0), linestyle=':')

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
    parser.add_argument('log1')
    parser.add_argument('log2')
    args = parser.parse_args()

    df1 = load_file(args.log1)
    df2 = load_file(args.log2)

    configure_matplotlib()
    make_figure(df1, df2, args.output)

    abs_dest = os.path.abspath(args.output)
    try:
        browser = webbrowser.get('firefox')
        browser.open('file://' + abs_dest)
    except webbrowser.Error:
        print(abs_dest)


if __name__ == '__main__':
    main()
