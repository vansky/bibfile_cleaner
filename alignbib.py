# python alignbib.py bibfile outbibfile
# aligns bibfile IDs to a unified format
#  best used on a new bibfile before merging it into an existing bibfile
#  that way, no existing bib refs in your papers will be broken

#  use idformat function to specify desired id format

import re
import sys

def idformat(entry):
  #formats the bib ID based on this spec;
  #default is schulerlab format: last1(last2|etal)year3year4
  if 'author' in entry and 'year' in entry:
    #standard format only exists when there are authors and a year
    authors = entry['author'].split(' and ')
    for aix,author in enumerate(authors):
      sauth = author.split(',')
      authors[aix] = (sauth[1].strip(), cleanchars(sauth[0].strip().strip('{}'))) #(first, last)
    if len(authors) > 2:
      #et al case
      entry['id'] = authors[0][1].lower().replace(' ','') + 'etal' + entry['year'][-2:]+','
    elif len(authors) > 1:
      #two author case
      entry['id'] = authors[0][1].lower().replace(' ','') + authors[1][1].lower().replace(' ','') + entry['year'][-2:]+','
    else:
      #solo author case
      entry['id'] = authors[0][1].lower().replace(' ','') + entry['year'][-2:]+','
  return entry

def cleanchars(instr):
  #remove international symbols/diacritics from names before using them as IDs
  outstr = []
  cix = 0
  while cix < len(instr): 
    if instr[cix] == '\\':
      if instr[cix+2] == '{':
        #the escaped portion is in braces
        endix = instr.find('}',cix+3)
        if endix == -1:
          outstr.append(instr[cix+3:])
          break
        outstr.append(instr[cix+3:endix])
        cix = endix
      else:
        #only one char is escaped
        outstr.append(instr[cix+2])
        cix += 2
    else:
      outstr.append(instr[cix])
    cix += 1
  return ''.join(outstr)

def addentry(entry,outbib,entryid):
  #adds an entry to a given bibdict
  dentry = dict(entry)
  for tag in dentry:
    if tag in ('type','id'):
      continue
    if dentry[tag][-1] == ',':
      #need to omit the final comma
      if not dentry[tag][0].isalnum() and (
        (dentry[tag][0] == dentry[tag][-2] in ('"',"'")) or
        (dentry[tag][0] == '{' and dentry[tag][-2] == '}')):
          #need to remove first and last char (likely "",'', or {})
        dentry[tag] = dentry[tag][1:-2]
      else:
        #only need to remove final comma
        dentry[tag] = dentry[tag][0:-1]
    else:
      if not dentry[tag][0].isalnum() and (
        (dentry[tag][0] == dentry[tag][-1] in ('"',"'")) or
        (dentry[tag][0] == '{' and dentry[tag][-1] == '}')):
        #need to remove first and last char (likely "",'', or {})
        dentry[tag] = dentry[tag][1:-1]
  if 'author' in dentry:
    dentry['author'] = stringauth(stdauth(dentry['author']))
    dentry = idformat(dentry)
    if dentry['author'] not in authordups:
      authordups[dentry['author']] = []
    authordups[dentry['author']] = (dentry['id'],entryid) #add entryid to the list of possible dups for these authors
  outbib[(dentry['id'],entryid)] = dentry

def alphabetize(outbib):
  #converts a dict with arbitrary unique keys to an alphabetized list of entry dicts
  output = []
  keys = sorted(outbib)
  for key in keys: #(id, autokey)
    output.append(outbib[key])
  namekeys = zip(*keys)[0]
  print 'Duplicate IDs: ', list(set([n[:-1] for n in namekeys if namekeys.count( n ) > 1]))
  return output

def stdauth(instr):
  #convert a string form of author bib info to a list of tuples
  stringlist = instr.replace('$\\backslash$','\\').split(' and ')
  tuplelist = []
  for s in stringlist:
    comma = s.find(',')
    if comma != -1:
      #format is last, first
      tuplelist.append((s[comma+1:].strip(), s[:comma].strip().strip('{}')) )
    else:
      #format is first middles last
      opbrack = s.find(' {')
      #assume brackets will only be used around last name
      if opbrack != -1:
        #format is first middles {last}
        tuplelist.append((s[:opbrack].strip(), s[opbrack+1:].strip().strip('{}')) )
      else:
        sstr = s.split()
        tuplelist.append((' '.join(sstr[:-1]).strip(),sstr[-1].strip()) )
  return tuplelist

def stringauth(inlist):
  #convert a list of author tuples to a string
  outlist = []
  for auth in inlist:
    if len(auth[1]) > 3 and auth[1][-2] == '{':
      #final char has a diacritic, so replace the real final brace
      outlist.append('{'+auth[1]+'}}, '+auth[0])
    else:
      outlist.append('{'+auth[1]+'}, '+auth[0])
  return ' and '.join(outlist)

if len(sys.argv) < 3:
  print 'Too few args'
  raise

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
  if sline in ['','}']:
    continue
  elif sline[0] == '%':
    #comment line; likely an alphabetic index marker; throw it out;
    continue
  elif sline == 'EOF':
    #add final entry
    addentry(entry, outbib, entryid)
    entryid += 1
  elif sline[0] == '@':
    #starting a new entry
    if entry != []:
      #there's an actual entry to store
      addentry(entry, outbib, entryid)
      entryid += 1
    entry = []
    
    if sline[1:7] == 'string':
      #just a string macro
      strings.append(sline)
    else:
      #start an entry
      firstbrack = sline.find('{')
      entry.append(('type', sline[:firstbrack].strip().lower()))
      entry.append(('id', sline[firstbrack+1:].strip().lower()))
  else:
    #continue to build entry
    tagbreak = sline.find('=')
    if tagbreak == -1:
      #continue the previous tag entry
      entry[-1] = (entry[-1][0], entry[-1][1] + ' ' + sline)
    else:
      #start a new tag entry
      entry.append( (sline[:tagbreak].lower().strip(), sline[tagbreak+1:].strip()) )

#check for duplicates
output = alphabetize(outbib)

alphatag = ''

with open(sys.argv[2],'w') as f:
  for s in strings:
    #output string macros first
    f.write(s+'\n\n')
    
  for entry in output:
    if entry['id'][0].upper() != alphatag:
      alphatag = entry['id'][0].upper()
      f.write('%'+alphatag*3+'\n\n')
    f.write(entry['type'] + '{' + entry['id'][:-1]+',\n')
    keys = sorted(entry)
    keys.remove('type')
    keys.remove('id')
    if 'file' in keys:
      keys.remove('file') #since you'll really only do this when merging another bibfile, get rid of the other person's Mendeley info
    lastkey = keys[-1]
    for key in keys:
      if key == lastkey:
        f.write('  '+key+' = {'+entry[key]+'}\n')
      else:
        f.write('  '+key+' = {'+entry[key]+'},\n')
    f.write('}\n\n')
      
