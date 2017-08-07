#! /usr/bin/env python

import csv
import re
import ast
import ssl
import xml.etree.ElementTree as ET
from urllib import request
from urllib.request import urlopen
from pymarc import Record, Field, marcxml

# This is stupid. Certificate issues are going to drive me bonkers.
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

languages = {
  'arabic': { 'short': 'ar', 'mid': 'ara', 'long': 'Arabic', 'orig': 'العربية'},
  'chinese': { 'short': 'zh', 'mid': 'chi', 'long': 'Chinese', 'orig': '中文'},
  'english': { 'short': 'en', 'mid': 'eng', 'long': 'English', 'orig': 'English'},
  'french': { 'short': 'fr', 'mid': 'fre', 'long': 'French', 'orig': 'Français'},
  'russian': { 'short': 'ru', 'mid': 'rus', 'long': 'Russian', 'orig': 'Русский'},
  'spanish': { 'short': 'es', 'mid': 'spa', 'long': 'Spanish', 'orig': 'Español'},
  'ar': 'arabic',
  'zh': 'chinese',
  'en': 'english',
  'fr': 'french',
  'ru': 'russian',
  'es': 'spanish',
  'a': 'arabic',
  'c': 'chinese',
  'e': 'english',
  'f': 'french',
  'r': 'russian',
  's': 'spanish',
}

records_new = []
records_update = []
no_symbols = []

# First let's process our csv, unov_ds_analyzed.csv
# Fieldnames 191__a,71020a,65117a,71127a,65007a,245__,246__,246__(2),246__(3),079__,269__,coverage,500,020__a,022__a,en_id,fr_id,es_id,ru_id,dl
with open('unov_metadata.csv') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    if row['dl'] == 'y':
      records_update.append(row)
    else:
      records_new.append(row)

# we don't want to create fields for any of these, or we want to transform them first
skip_list = ['coverage','dl','en_id','fr_id','es_id','ru_id']
# let's isolate these so we can know how many files each record has
file_list = ['en_id','fr_id','es_id','ru_id']

# Read in our file_map.dat file once so we can just search it when we need to.
file_map = ast.literal_eval(open('file_map.dat','r').read())

# Now let's open a file so we can write out our new records. We'll do something similar for updates.
out_file = open('new.xml', 'wb+')
out_file.write(bytes('<?xml version="1.0"?>' + "\n", 'UTF-8'))
out_file.write(bytes("<collection>\n",'UTF-8'))
for r in records_new:
  record = Record()
  for k in r.keys():
    if k not in skip_list and len(r[k]) > 0:
      # first deal with the tags that have no indicators
      field,subfield = '',''
      ind = ' ',' '
      field_subfield = k.split('__')
      if len(field_subfield) == 1:
        # what's left has indicators...
        # e.g., ['65117a']
        field = field_subfield[0][0:3]
        ind = list(field_subfield[0][3:5])
        subfield = field_subfield[0][5]
        if '||' in r[k]:
          for multi_val in r[k].split('||'):
            record.add_field(Field(tag=field,indicators=ind,subfields=[subfield,multi_val]))
        else:
          record.add_field(Field(tag=field,indicators=ind,subfields=[subfield,r[k]]))
      else:
        field,subfield = field_subfield
        if '(' in subfield: 
          subfield = ''
        ind = [' ',' ']
        # for 245 and 246, we have potential for multiple subfields, $a, $b, etc.
        if '$' in r[k]:
          s_fields = []
          k_values = re.split("(\$[a-z]\s)",r[k])
          # for some reason there's a leading space, which gets thrown into list id 0 
          k_values.pop(0)
          for idx, val in enumerate(k_values):
            if '$' in val:
              #this is the subfield characater
              s_fields.append(val[1])
              s_fields.append(k_values[idx+1])
          record.add_field(Field(tag=field,indicators=ind,subfields=s_fields))
        else:
          if '||' in r[k]:
            for multi_val in r[k].split('||'):
              record.add_field(Field(tag=field,indicators=ind,subfields=[subfield,multi_val]))
          else:
            record.add_field(Field(tag=field,indicators=ind,subfields=[subfield,r[k]]))

  # Now let's grab authority codes for 650 and 651 fields. These are stored in pre-populated files.

  a650s = ast.literal_eval(open('a650.dat','r').read())
  a651s = ast.literal_eval(open('a651.dat','r').read())

  for f in record.get_fields('650'):
    lookup = f['a'].strip()
    auth_code = a650s[lookup]
    #print(auth_code)
    record[f.tag].add_subfield('0',auth_code)

  # Completely unsurprisingly, 651 is different.
  for f in record.get_fields('651'):
    lookup = f['a'].strip()
    auth_code = a651s[lookup]
    #print(auth_code)
    record[f.tag].add_subfield('0',auth_code)


  this_symbol = record['191']['a']
  #print(this_symbol)
  this_files = ''
  try:
    files = file_map[this_symbol]['files']
  except KeyError:
    print("Unable to find any file listings for this record:")
    print(record)
    pass

  ffts = {}
  for lang in ['en','fr','es','ru']:
    if len(r[lang + "_id"]) > 0:
      # this languages is included ...
      this_language = languages[languages[lang]]['orig']
      ffts[this_language] = []

  for f in files:
    # try to determine the language so it can be added to the FFT field
    this_language = f.split('.pdf')[0].split("/")[-1][-1]
    if this_language in ['a','c','e','f','r','s']:
      fft_language = languages[languages[this_language]]['orig']
      try:
        ffts[fft_language].append(f)
      except KeyError:
        # We seem to be missing this file in our languages list ...
        ffts[fft_language] = [f]

  for fft in ffts:
    if ffts[fft]:
      this_subfields = ['a', ffts[fft][0], 'd', fft, 'n', str(ffts[fft]).split("/")[-1]]
      #print(this_subfields)
      record.add_field(Field(tag='FFT', indicators=[' ',' '], subfields=this_subfields))

  out_file.write(marcxml.record_to_xml(record))
  #print(record)
out_file.write(bytes("</collection>",'UTF-8'))
out_file.close()
