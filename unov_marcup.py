#! /usr/bin/env python
#encoding: utf-8

import csv
import ast
import re
from pymarc import Record, Field, marcxml

# Setup

# we don't want to create fields for any of these, or we want to transform them first
skip_list = ['coverage','dl','en_id','fr_id','es_id','ru_id']
# let's isolate these so we can know how many files each record has
file_list = ['en_id','fr_id','es_id','ru_id']
new_records = []
update_records = []

#These are lookup files
symbol_map = ast.literal_eval(open('symbol_map.dat','r').read())
file_map = ast.literal_eval(open('file_map.dat','r').read())
a650s = ast.literal_eval(open('a650.dat','r').read())
a651s = ast.literal_eval(open('a651.dat','r').read())

languages = {
  'arabic': { 'short': 'ar', 'mid': 'ara', 'long': 'Arabic', 'orig': 'ﺎﻠﻋﺮﺒﻳﺓ'},
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

def map_to_marc(r):
  record = Record()
  for k in r.keys():
    if k not in skip_list and len(r[k]) > 0:
      field,subfield = '',''
      ind = ' ',' '
      field_subfield = k.split('__')
      if len(field_subfield) == 1:
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
  for f in record.get_fields('650'):
    lookup = f['a'].strip()
    auth_code = a650s[lookup]
    record[f.tag].add_subfield('0',auth_code)

  for f in record.get_fields('651'):
    lookup = f['a'].strip()
    auth_code = a651s[lookup]
    #print(auth_code)
    record[f.tag].add_subfield('0',auth_code)

  # Add 980
  record.add_field(Field(tag='980', indicators=[' ',' '], subfields=['a','UNOV']))

  # Add 989
  record.add_field(Field(tag='989', indicators=[' ',' '], subfields=['a','Documents and Publications']))

  files = ''
  this_symbol = record['191']['a']
  if this_symbol in file_map.keys():
    files = file_map[this_symbol]['files']
  elif this_symbol.replace('E/NL.','E/NL/') in file_map.keys():
    files = file_map[this_symbol.replace('E/NL.','E/NL/')]['files']
  else:
    print("Unable to find any file listings for this record:", record)

  # Now FFTs
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
      this_subfields = ['a', ffts[fft][0], 'd', fft, 'n', str(ffts[fft]).split("/")[-1].split("'")[0]]
      #print(this_subfields)
      record.add_field(Field(tag='FFT', indicators=[' ',' '], subfields=this_subfields))

  return record

# Open our csv and process each row
with open('unov_metadata.csv', encoding='utf-8') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    this_record = map_to_marc(row)

    # Now figure out whether this is new or updated
    this_symbol = this_record['191']['a']
    if this_symbol in symbol_map.keys():
      # Definitely an update
      this_record.add_field(Field(tag='001', data=symbol_map[this_symbol]))
      # 999 depends on update vs new
      this_record.add_field(Field(tag='999', indicators=[' ',' '], subfields=['a','dlu20170809','b','20170809','c','u']))
      update_records.append(this_record)
    elif this_symbol.replace('E/NL.','E/NL/') in symbol_map.keys():
      # Also definitely an update
      this_record.add_field(Field(tag='001', data=symbol_map[this_symbol.replace('E/NL.','E/NL/')]))
      this_record.add_field(Field(tag='999', indicators=[' ',' '], subfields=['a','dlu20170810','b','20170810','c','u']))
      update_records.append(this_record)
    else:
      # Definitely new
      this_record.add_field(Field(tag='999', indicators=[' ',' '], subfields=['a','dlo20170810','b','20170810','c','o']))
      new_records.append(this_record)

print("New:",len(new_records))
print("Updates:",len(update_records))

with open('new.xml','wb+') as f:
  f.write(bytes('<?xml version="1.0"?>' + "\n", 'UTF-8'))
  f.write(bytes("<collection>\n",'UTF-8'))
  for record in new_records:
    f.write(marcxml.record_to_xml(record, encoding='utf-8'))
    f.write(bytes("\n","UTF-8"))
  f.write(bytes("</collection>",'UTF-8'))

with open('update.xml','wb+') as f:
  f.write(bytes('<?xml version="1.0"?>' + "\n", 'UTF-8'))
  f.write(bytes("<collection>\n",'UTF-8'))
  for record in update_records:
    f.write(marcxml.record_to_xml(record, encoding='utf-8'))
    f.write(bytes("\n","UTF-8"))
  f.write(bytes("</collection>",'UTF-8'))
