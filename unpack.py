#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
from collections import defaultdict
from typing import List, Dict, Set, Any, TextIO, Tuple

import pandas as pd


def arrange_fields(fields: Set[str]) -> List[str]:
    fields.remove('t')
    return ['t'] + list(sorted(fields))


def split_fields(fields: List[str]) -> Dict[str, Any]:
    info = {}
    for field in fields:
        k, v = field.split('=')
        if k == 't':
            info[k] = datetime.datetime.fromtimestamp(float(v))
        else:
            info[k] = int(v, 10)
    return info


def load_events(infile: TextIO) -> Tuple[List[datetime.datetime], Dict[
        str, List[Dict[str, Any]]], Dict[str, List[str]]]:
    data = defaultdict(list)
    event_fields = defaultdict(set)
    times = []
    for line in infile:
        fields = line.rstrip().split()
        event = fields.pop(0)
        info = split_fields(fields)

        if event == 'time':
            times.append(info['t'])
        elif event == 'finish_ibd':
            break
        else:
            data[event].append(info)

        # track all the known fields
        for k in info:
            event_fields[event].add(k)

    event_fields = {k: list(sorted(v)) for k, v in event_fields.items()}
    return times, dict(data), event_fields


def create_flushes_frame(flushes: List[Dict[str, Any]]) -> pd.DataFrame:
    times = [flush['t'] for flush in flushes]
    frame = pd.DataFrame(flushes, index=times)
    columns = frame.columns.tolist()
    columns.remove('t')
    return frame[columns]


def create_frame(times: List[datetime.datetime], data: List[Dict[str, Any]],
                 columns: List[str]):
    assert len(times) == len(data)
    for row in data:
        for col in columns:
            row.setdefault(col, None)
    return pd.DataFrame(data, index=times)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--output', default='data.pkl', help='Outpu .csv name')
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename) as infile:
        times, events, event_fields = load_events(infile)

    frames = {}
    frames['flushes'] = create_flushes_frame(events.pop('flush'))

    for event, data in events.items():
        frames[event] = create_frame(times, data, event_fields[event])

    with open(args.output, 'wb') as outfile:
        save_data = {'filename': args.filename, 'frames': frames}
        pickle.dump(save_data, outfile)


if __name__ == '__main__':
    main()
