#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
import os
import re
from collections import defaultdict
from typing import List, Dict, Set, Any, TextIO, Tuple, Optional, Union

import pandas as pd

# Expected sections in the input file to remap
EXPECTED_SECTIONS = 2

FILE_RE = re.compile(r'^.*?-(\d+)\.log$')

Field = Union[datetime.datetime, int]


def arrange_fields(fields: Set[str]) -> List[str]:
    fields.remove('t')
    return ['t'] + list(sorted(fields))


def split_fields(fields: List[str]) -> Dict[str, Field]:
    info = {}
    for field in fields:
        k, v = field.split('=')
        val = 0  # type: Field
        if k == 't':
            val = datetime.datetime.fromtimestamp(float(v))
        else:
            val = int(v, 10)
        info[k] = val
    return info


class EventData:
    def __init__(self):
        self.git = ''
        self.config = ''
        self.times = []  # type: List[datetime.datetime]
        self.events = {}  # type: Dict[str, List[Dict[str, Field]]]
        self.event_fields = {}  # type: Dict[str, List[str]]


def load_events(infile: TextIO) -> EventData:
    events = defaultdict(list)
    event_fields = defaultdict(set)
    section = 0

    output = EventData()

    for line in infile:
        line = line.strip()
        if not line:
            continue
        elif line.startswith('---'):
            section += 1
            continue

        if section == 0:
            output.git = line
            continue
        elif section == 1:
            output.config += line + '\n'
            continue

        fields = line.split()
        event = fields.pop(0)
        info = split_fields(fields)

        if event == 'begin':
            continue
        elif event == 'time':
            output.times.append(info['t'])  # type: ignore
        elif event == 'finish':
            break
        else:
            events[event].append(info)

        # track all the known fields
        for k in info:
            event_fields[event].add(k)

    output.event_fields = {k: list(sorted(v)) for k, v in event_fields.items()}
    output.events = dict(events)
    return output


def create_flushes_frame(flushes: List[Dict[str, Field]]) -> pd.DataFrame:
    times = [flush['t'] for flush in flushes]
    frame = pd.DataFrame(flushes, index=times)
    columns = frame.columns.tolist()
    columns.remove('t')
    return frame[columns]


def create_frame(times: List[datetime.datetime], data: List[Dict[str, Field]],
                 columns: List[str]) -> pd.DataFrame:
    assert len(times) == len(data)
    for row in data:
        for col in columns:
            row.setdefault(col, None)
    return pd.DataFrame(data, index=times)


def choose_input() -> str:
    """Choose a good input file to process."""
    logsdir = os.path.expanduser('~/logs')
    best_timestamp = 0
    for f in os.listdir(logsdir):
        m = FILE_RE.match(f)
        if m:
            ts_str, = m.groups()
            ts = int(ts_str, 10)
            if ts > best_timestamp:
                best_timestamp = ts
                logfile = os.path.join(logsdir, f)
    if logfile is None:
        raise ValueError(
            'Failed to autodetect input file, please specify one with -f')
    return logfile


def choose_output(input_file: str) -> str:
    """Choose a good name for the output file."""
    outdir = os.path.abspath(os.path.dirname(input_file))
    prefix = input_file.split('.')[0]
    savefile = os.path.join(outdir, prefix + '.pkl')
    return savefile


def unpack_data_strict(input_file: str) -> Dict[str, Any]:
    with open(input_file) as infile:
        data = load_events(infile)

    frames = {}
    try:
        frames['flushes'] = create_flushes_frame(data.events.pop('flush'))
    except KeyError:
        print('WARNING: no flush events')

    for event, vec in data.events.items():
        frames[event] = create_frame(data.times, vec, data.event_fields[event])

    return {
        'filename': input_file,
        'frames': frames,
        'git': data.git,
        'config': data.config
    }


def unpack_data() -> Dict[str, Any]:
    input_file = choose_input()
    assert input_file is not None
    print('Loading data from input file {}'.format(input_file))
    return unpack_data_strict(input_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='Output pkl name')
    parser.add_argument('-f', '--file', help='File to process')
    args = parser.parse_args()

    if args.file is not None:
        logfile = args.file
    else:
        logfile = choose_input()
        print('using logfile {}'.format(logfile))

    save_data = unpack_data_strict(logfile)

    if args.output is not None:
        savefile = args.output
    else:
        savefile = choose_output(logfile)
        print('saving output to {}'.format(savefile))

    with open(savefile, 'wb') as outfile:
        pickle.dump(save_data, outfile)


if __name__ == '__main__':
    main()
