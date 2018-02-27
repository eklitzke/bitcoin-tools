import sys


def dofile(fileobj):
    commits = []
    testnames = set()
    times = {}
    basetime = {}

    for line in fileobj:
        line = line.strip()
        if not line:
            continue
        elif line.startswith('git '):
            commit = line.split()[-1]
            commits.append(commit)
        elif line.startswith('#'):
            continue
        else:
            parts = line.split(', ')
            test = parts[0]
            median = float(parts[-1])
            testnames.add(test)
            times[(commit, test)] = median
            if test not in basetime:
                basetime[test] = median

    testnames = list(sorted(testnames))
    print(
        'Commit     Test                                     Median (s)   Speedup'
    )
    print(
        '------------------------------------------------------------------------'
    )
    for commit in commits:
        for test in testnames:
            time = times[(commit, test)]
            base = basetime[test]
            ratio = base / time
            print('%-10s %-40s %-1.5e  %5.2fx' % (commit[:6], test, time,
                                                  ratio))


def main():
    for f in ['gcc48.txt', 'gcc73.txt']:
        print(f)
        print()
        with open(f) as fileobj:
            dofile(fileobj)
            print()


if __name__ == '__main__':
    main()
