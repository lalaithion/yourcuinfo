#!/usr/bin/python3
import sys, json
from collections import defaultdict

def sectionByNumber(sections, num):
    for section in sections:
        if section['number'] == num:
            return section
    return None

def main():
    if len(sys.argv) < 3:
        print('Usage: %s oldfile.json newfile.json' % sys.argv[0])
        return
    with open(sys.argv[1]) as f:
        olddata = json.loads(f.read())
    with open(sys.argv[2]) as f:
        newdata = json.loads(f.read())

    removed = []
    added = []
    changed = defaultdict(list)
    for name, data in olddata.items():
        if name not in newdata:
            removed.append(name)
        else:
            for section in data['sections']:
                newsection = sectionByNumber(newdata[name]['sections'],
                        section['number'])

                ident = '%s - %s' % (name, section['number'])
                if newsection is None:
                    removed.append(ident)
                else:
                    for k, v in section.items():
                        newv = newsection[k]
                        if v != newv:
                            changed[ident].append('%s: %s > %s' % (k, v, newv))
    for name, data in newdata.items():
        if name not in olddata:
            added.append(name)
        else:
            for section in data['sections']:
                oldsection = sectionByNumber(olddata[name]['sections'],
                        section['number'])
                if oldsection is None:
                    added.append('%s - %s' % (name, section['number']))

    if len(added) is len(removed) is len(changed) is 0:
        return 1
    print('\n   '.join(['Added:'] + added))
    print('\n   '.join(['Removed:'] + removed))
    print('\n   '.join(['Changed:'] + [
            '\n      '.join(['%s:' % name] + values)
            for name, values in changed.items()]))
    return 0

if __name__ == '__main__':
    exit(main())
