#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
import os
import re
from collections import defaultdict
from typing import List, Dict, Set, Any, TextIO, Tuple

import pandas as pd

# Expected sections in the input file to remap
EXPECTED_SECTIONS = 2

FILE_RE = re.compile(r'^.*?-(\d+)\.log$')


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
    section = 0
    for line in infile:
        if line.startswith('----'):
            section += 1
            continue
        elif section < EXPECTED_SECTIONS:
            continue

        fields = line.rstrip().split()
        event = fields.pop(0)
        info = split_fields(fields)

        if event == 'begin':
            continue
        elif event == 'time':
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
        '-o', '--output', default='data.pkl', help='Output .csv name')
    parser.add_argument('-f', '--file', help='File to process')
    args = parser.parse_args()

    logfile = args.file if args.file is not None else None
    if logfile is None:
        logsdir = os.path.expanduser('~/logs')
        best_timestamp = 0
        for f in os.listdir(logsdir):
            m = FILE_RE.match(f)
            if m:
                ts, = m.groups()
                ts = int(ts, 10)
                if ts > best_timestamp:
                    best_timestamp = ts
                    logfile = os.path.join(logsdir, f)
        if logfile is None:
            parser.error(
                'Failed to autodetect input file, please specify one with -f')
        else:
            print('using logfile {}'.format(logfile))

    with open(logfile) as infile:
        times, events, event_fields = load_events(infile)

    frames = {}
    try:
        frames['flushes'] = create_flushes_frame(events.pop('flush'))
    except KeyError:
        print('WARNING: no flush events')

    for event, data in events.items():
        frames[event] = create_frame(times, data, event_fields[event])

    with open(args.output, 'wb') as outfile:
        save_data = {'filename': logfile, 'frames': frames}
        pickle.dump(save_data, outfile)


if __name__ == '__main__':
    main()
