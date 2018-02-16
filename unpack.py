#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import re
import pickle
from collections import defaultdict
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd

INT_RE = re.compile(r'^\d+$')
FLOAT_RE = re.compile(r'^\d+\.\d+$')

IGNORE_FIELDS = frozenset(['progress'])
IGNORE_EVENTS = frozenset(['finish_ibd'])


def create_dataframe(fields: List[str],
                     data: List[Tuple[int, Dict[str, int]]]) -> np.ndarray:
    vec = []
    for ts, info in data:
        vec.append([ts] + [info.get(k, 0) for k in fields])
    return np.array(vec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', default='data.pkl', help='Outpu .csv name')
    parser.add_argument('filename')
    args = parser.parse_args()

    events = defaultdict(list)
    event_fields = defaultdict(set)

    with open(args.filename) as infile:
        for line in infile:
            fields = line.rstrip().split()
            info = {}
            event = None
            ts = None
            for field in fields:
                k, v = field.split('=')
                if k in IGNORE_FIELDS:
                    continue
                elif k == 't':
                    ts = int(float(v) * 1e9)
                elif k == 'event':
                    event = v
                else:
                    info[k] = int(v, 10)
            assert ts and event
            if event in IGNORE_EVENTS:
                continue
            for k, v in info.items():
                event_fields[event].add(k)
            events[event].append((ts, info))

    frames = {}
    for event, data in events.items():
        fields = list(event_fields[event])
        vec = create_dataframe(fields, data)
        frame = pd.DataFrame(vec, columns=['t'] + fields)
        frames[event] = frame

    with open(args.output, 'wb') as outfile:
        pickle.dump(frames, outfile)


if __name__ == '__main__':
    main()
