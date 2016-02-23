#!/usr/bin/env python

# python cleanbib.py bibfile outbibfile
# cleans bibtex bibfiles
#  alphabetizes entries
#  separates alphabetical sections with %XXX for easy browsing
#  converts all keys to lowercase for consistency
#  reports duplicate bib IDs
#  standardizes author formats
#  TODO: reports probability of duplicate entries based on key-value overlap

# Make Python 3 notation compatible with Python 2
from __future__ import print_function
# Likewise, use the same kind of zip function in both versions
try:
    import itertools.izip as zip
except ImportError:
    pass

# Regular imports
import sys


def addentry(entry, outbib, entryid):
    # adds an entry to a given bibdict
    dentry = dict(entry)
    for tag in dentry:
        if tag in ('type', 'id'):
            continue
        if dentry[tag][-1] == ',':
            # need to omit the final comma
            if not dentry[tag][0].isalnum() and (
                        (dentry[tag][0] == dentry[tag][-2] in ('"', "'")) or
                        (dentry[tag][0] == '{' and dentry[tag][-2] == '}')):
                # need to remove first and last char (likely "",'', or {})
                dentry[tag] = dentry[tag][1:-2]
            else:
                # only need to remove final comma
                dentry[tag] = dentry[tag][0:-1]
        else:
            if not dentry[tag][0].isalnum() and (
                        (dentry[tag][0] == dentry[tag][-1] in ('"', "'")) or
                        (dentry[tag][0] == '{' and dentry[tag][-1] == '}')):
                # need to remove first and last char (likely "",'', or {})
                dentry[tag] = dentry[tag][1:-1]
    if 'author' in dentry:
        dentry['author'] = stringauth(stdauth(dentry['author']))
        if dentry['author'] not in authordups:
            authordups[dentry['author']] = []
        # add entryid to the list of possible dups for these authors
        authordups[dentry['author']] = (dentry['id'], entryid)
    try:
        outbib[(dentry['id'], entryid)] = dentry
    except KeyError:
        print(dentry)


def alphabetize(outbib):
    # converts a dict with arbitrary unique keys to an alphabetized list of entry dicts
    output = []
    keys = sorted(outbib)
    for key in keys:  # (id, autokey)
        output.append(outbib[key])
    namekeys = list(zip(*keys))[0]
    print('Duplicate IDs: ', sorted(list(set([n[:-1] for n in namekeys if namekeys.count(n) > 1]))))
    return output


def reportdups(outbib, authordups):
    # report probability of duplicate entries
    print('Probabilistic duplicate reporting not currently implemented')
    pass


def stdauth(instr):
    # convert a string form of author bib info to a list of tuples
    stringlist = instr.replace('$\\backslash$', '\\').split(' and ')
    tuplelist = []
    for s in stringlist:
        comma = s.find(',')
        if comma != -1:
            # format is last, first
            tuplelist.append((s[comma + 1:].strip().strip('{}'), s[:comma].strip().strip('{}')))
        else:
            # format is first middles last
            opbrack = s.find(' {')
            # assume brackets will only be used around last name
            if opbrack != -1:
                # format is first middles {last}
                tuplelist.append((s[:opbrack].strip().strip('{}'), s[opbrack + 1:].strip().strip('{}')))
            else:
                sstr = s.split()
                tuplelist.append((' '.join(sstr[:-1]).strip(), sstr[-1].strip()))
    return tuplelist


def stringauth(inlist):
    # convert a list of author tuples to a string
    outlist = []
    for auth in inlist:
        first = auth[0]
        last = auth[1]
        if len(last) > 3 and last[-2] == '{':
            # final char has a diacritic, so replace the real final brace
            last = last + '}'
        if len(first) > 3 and first[-2] == '{':
            # final char has a diacritic, so replace the real final brace
            first = first + '}'
        outlist.append('{' + last + '}, ' + first)
    return ' and '.join(outlist)


if len(sys.argv) < 3:
    print('Too few args')
    exit()

with open(sys.argv[1], 'r') as f:
    biblines = f.readlines()

outbib = {}
strings = []
authordups = {}
entry = []
entryid = 0

biblines.append('\nEOF\n')
for line in biblines:
    sline = line.strip()
    if sline in ['', '}']:
        continue
    elif sline[0] == '%':
        # comment line; likely an alphabetic index marker; throw it out;
        continue
    elif sline == 'EOF':
        # add final entry
        addentry(entry, outbib, entryid)
        entryid += 1
    elif sline[0] == '@':
        # starting a new entry
        if entry != []:
            # there's an actual entry to store
            addentry(entry, outbib, entryid)
            entryid += 1
        entry = []

        if sline[1:7] == 'string':
            # just a string macro
            strings.append(sline)
        else:
            # start an entry
            firstbrack = sline.find('{')
            entry.append(('type', sline[:firstbrack].strip().lower()))
            entry.append(('id', sline[firstbrack + 1:].strip().lower()))
    else:
        # continue to build entry
        tagbreak = sline.find('=')
        if tagbreak == -1 and len(entry) > 0:
            # continue the previous tag entry
            entry[-1] = (entry[-1][0], entry[-1][1] + ' ' + sline)
        else:
            # start a new tag entry
            entry.append((sline[:tagbreak].lower().strip(), sline[tagbreak + 1:].strip()))

# check for duplicates
reportdups(outbib, authordups)
output = alphabetize(outbib)

alphatag = ''

with open(sys.argv[2], 'w') as f:
    for s in strings:
        # output string macros first
        f.write(s + '\n\n')

    for entry in output:
        if entry['id'][0].upper() != alphatag:
            alphatag = entry['id'][0].upper()
            f.write('%{0}{0}{0}\n\n'.format((alphatag)))
        f.write(entry['type'] + '{' + entry['id'][:-1] + ',\n')
        keys = sorted(entry)
        keys.remove('type')
        keys.remove('id')
        lastkey = keys[-1]
        #    if 'year' in entry and entry['year'][-1] == '}':
        #      #handle case where entry wasn't ended on a newline
        #      entry['year'] = entry['year'][:-1]
        for key in keys:
            if entry[key].count('{') != entry[key].count('}') and entry[key][-1] == '}':
                # handle case where entry wasn't ended on a newline; especially bad with BibDesk
                entry[key] = entry[key][:-1]
            if key == lastkey:
                f.write('  ' + key + ' = {' + entry[key] + '}\n')
            else:
                f.write('  ' + key + ' = {' + entry[key] + '},\n')
        f.write('}\n\n')
