# python cleanbib.py bibfile outbibfile
# USE: cleans bibtex bibfiles
#  alphabetizes entries
#  separates alphabetical sections with %XXX for easy browsing
#  converts all keys to lowercase for consistency
#  reports duplicate bib IDs
#  TODO: standardizes author formats
#  TODO: reports probability of duplicate entries based on key-value overlap

import sys

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
  if 'authors' in dentry:
    dentry['authors'] = stringauth(stdauth(dentry['authors']))
    if dentry['authors'] not in authordups:
      authordups[dentry['authors']] = []
    authordups[dentry['authors']] = (dentry['id'],entryid) #add entryid to the list of possible dups for these authors
  outbib[(dentry['id'],entryid)] = dentry

def alphabetize(outbib):
  #converts a dict with arbitrary unique keys to an alphabetized list of entry dicts
  output = []
  keys = sorted(outbib)
  for key in keys: #(id, autokey)
    output.append(outbib[key])
  namekeys = zip(*keys)[0]
  print 'Duplicate IDs: ', list(set([n for n in namekeys if namekeys.count( n ) > 1]))
  return output

def reportdups(outbib, authordups):
  #report probability of duplicate entries
  print 'Duplicate reporting not currently implemented'
  pass

def stdauth(instr):
  #convert a string form of author bib info to a list of tuples
  #stringlist = instr.split(' and ')
  #tuplelist = []
  #for s in stringlist:
  #  comma = s.find(',')
  #  if comma != -1:
  #    #format is last, first
  #    tuplelist.append((s[comma+1:].strip(), s[:comma].strip()) )
  #  else:
  #    #format is first last
  return instr

def stringauth(inlist):
  #convert a list of author tuples to a string
  #raise
  return inlist

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
reportdups(outbib, authordups)
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
    lastkey = keys[-1]
    for key in keys:
      if key == lastkey:
        f.write('  '+key+' = {'+entry[key]+'}\n')
      else:
        f.write('  '+key+' = {'+entry[key]+'},\n')
    f.write('}\n\n')
      
