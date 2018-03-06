#!/usr/bin/env python3
#
# Script to unpack data from stap into pandas frames.

import argparse
import pickle
import datetime
import os
import re
from collections import defaultdict
from typing import List, Dict, Set, Any, TextIO, Union

import pandas as pd

# Expected sections in the input file to remap
EXPECTED_SECTIONS = 2

SECTION_RE = re.compile(r'^--- ([a-z]+)$')
HOST_RE = re.compile(r'^([a-zA-Z0-9.-]+)-\d+\.log$')
FILE_RE = re.compile(r'^.*?-(\d+)\.log$')

Field = Union[datetime.datetime, pd.Timedelta, int, str, float]


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
        elif k == 'elapsed':
            val = datetime.timedelta(seconds=float(v))
        elif k == 'reason':
            val = v
        elif k == 'progress':
            val = float(v) / 1e6
        elif k.endswith(':time'):
            val = pd.Timedelta(int(v) * 1000, unit='ns')
        else:
            val = int(v, 10)
        info[k] = val
    return info


class EventData:
    def __init__(self):
        self.hostinfo = {}  # type: Dict[str, Field]
        self.config = ''
        self.flush_times = []  # type: List[datetime.datetime]
        self.data_times = []  # type: List[datetime.datetime]
        self.events = {}  # type: Dict[str, List[Dict[str, Field]]]
        self.event_fields = {}  # type: Dict[str, List[str]]


def load_events(infile: TextIO) -> EventData:
    events = defaultdict(list)  # type: Dict[str, List[Dict[str, Field]]]
    event_fields = defaultdict(set)  # type: Dict[str, Set[str]]
    section = ''

    output = EventData()

    for line in infile:
        line = line.strip()
        if not line:
            # ignore blank lines
            continue
        m = SECTION_RE.match(line)
        if m:
            section, = m.groups()
            continue

        if section == 'system':
            k, v = line.split(' ', 1)
            val = v  # type:Field
            if k.endswith(':bytes') or k.endswith(':count'):
                val = int(v)
            output.hostinfo[k] = val
            continue
        elif section == 'config':
            output.config += line + '\n'
            continue

        assert section == 'systemtap'
        fields = line.split()
        event = fields.pop(0)
        info = split_fields(fields)

        if event == 'begin':
            continue
        elif event == 'time':
            reason, t = info['reason'], info['elapsed']
            if reason == 'timer':
                output.data_times.append(t)
            elif reason == 'flush':
                output.flush_times.append(t)
            else:
                assert False
        elif event == 'finish':
            break
        else:
            # handle regular data
            events[event].append(info)
            for k in info:
                # track all the known fields
                event_fields[event].add(k)

    output.event_fields = {k: list(sorted(v)) for k, v in event_fields.items()}
    output.events = dict(events)
    return output


def create_flushes_frame(times: List[datetime.datetime],
                         flushes: List[Dict[str, Field]]) -> pd.DataFrame:
    frame = pd.DataFrame(flushes, index=times)
    columns = frame.columns.tolist()
    return frame[columns]


def create_frame(times: List[datetime.datetime], data: List[Dict[str, Field]],
                 columns: List[str]) -> pd.DataFrame:
    assert len(times) == len(data)
    for row in data:
        for col in columns:
            row.setdefault(col, None)
    return pd.DataFrame(data, index=times)


def choose_input(host: str = '') -> str:
    """Choose a good input file to process."""
    logsdir = os.path.expanduser('~/logs')
    best_timestamp = 0
    logfile = None
    for f in os.listdir(logsdir):
        if host:
            m = HOST_RE.match(f)
            if not m:
                continue
            file_host, = m.groups()
            if file_host != host:
                continue
        m = FILE_RE.match(f)
        if not m:
            continue
        ts_str, = m.groups()
        ts = int(ts_str, 10)
        if ts > best_timestamp:
            best_timestamp = ts
            logfile = os.path.join(logsdir, f)
    if logfile is None:
        raise ValueError('Failed to autodetect input file')
    return logfile


def choose_output(input_file: str) -> str:
    """Choose a good name for the output file."""
    outdir = os.path.abspath(os.path.dirname(input_file))
    prefix = input_file.split('.')[0]
    savefile = os.path.join(outdir, prefix + '.pkl')
    return savefile


def unpack_data_strict(input_file: str) -> Dict[str, Any]:
    if input_file.startswith('~'):
        input_file = os.path.expanduser(input_file)

    with open(input_file) as infile:
        data = load_events(infile)

    frames = {'flushes': None}
    try:
        frames['flushes'] = create_flushes_frame(data.flush_times,
                                                 data.events.pop('flush'))
    except KeyError:
        print('WARNING: no flush events')

    for event, vec in data.events.items():
        frames[event] = create_frame(data.data_times, vec,
                                     data.event_fields[event])

    return {
        'filename': input_file,
        'frames': frames,
        'hostinfo': data.hostinfo,
        'config': data.config
    }


def unpack_data(host: str = '') -> Dict[str, Any]:
    input_file = choose_input(host)
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
