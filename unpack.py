#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Set

import numpy as np
import pandas as pd

IGNORE_FIELDS = frozenset(['progress'])
IGNORE_EVENTS = frozenset(['finish_ibd'])


def create_dataframe(fields: List[str],
                     data: List[Tuple[int, Dict[str, int]]]) -> np.ndarray:
    vec = []
    for ts, info in data:
        vec.append([ts] + [info.get(k, 0) for k in fields])
    return np.array(vec)


def arrange_fields(fields: Set[str]) -> List[str]:
    fields.remove('t')
    return ['t'] + list(sorted(fields))


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
            for field in fields:
                k, v = field.split('=')
                if k in IGNORE_FIELDS:
                    continue
                elif k == 't':
                    info['t'] = datetime.datetime.fromtimestamp(float(v))
                elif k == 'event':
                    event = v
                else:
                    info[k] = int(v, 10)
            assert event
            if event in IGNORE_EVENTS:
                continue
            for k in info:
                event_fields[event].add(k)
            events[event].append(info)

    frames = {}
    for event, data in events.items():
        fields = arrange_fields(event_fields[event])
        for row in data:
            for field in fields:
                row.setdefault(field, 0)
        frame = pd.DataFrame(data)
        frames[event] = frame[fields]

    with open(args.output, 'wb') as outfile:
        pickle.dump(frames, outfile)


if __name__ == '__main__':
    main()
