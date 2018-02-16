#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
from collections import defaultdict
from typing import List, Dict, Set

import pandas as pd

IGNORE_EVENTS = frozenset(['finish_ibd'])


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
                if k == 't':
                    info['t'] = datetime.datetime.fromtimestamp(float(v))
                elif k == 'event':
                    event = v
                elif k == 'progress':
                    info[k] = float(v)
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
        fields = event_fields[event]
        times = []
        for row in data:
            for field in fields:
                row.setdefault(field, 0)
            times.append(row['t'])
        frame = pd.DataFrame(data, index=times)
        fields.remove('t')
        frames[event] = frame[sorted(fields)]

    with open(args.output, 'wb') as outfile:
        save_data = {'filename': args.filename, 'frames': frames}
        pickle.dump(save_data, outfile)


if __name__ == '__main__':
    main()
