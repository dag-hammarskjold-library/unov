#/usr/bin/env python

# get unov metadata files from S3: 0 - 4441
# https://s3.amazonaws.com/un-digital-library/unov/[num]/[contents, dublin_core.xml, metadata_undr.xml, handle]
#
# merge by symbol, with English as primary
#
# mapping:
# dc.coverage.temporal = ??
# dc.date.accessioned = ??
# dc.date.available = ??
# dc.date.issued = 269$a
# dc.language = 041$a<<
# English dc.title = 245
# Other dc.title = 246
# undr.identifier.symbol = 191

from urllib.request import urlopen
import xml.etree.ElementTree as ET
from pymarc import Record, Field, marcxml

languages = {
  'arabic': { 'short': 'ar', 'mid': 'ara', 'long': 'Arabic', 'orig': ''},
  'chinese': { 'short': 'zh', 'mid': 'chi', 'long': 'Chinese', 'orig': ''},
  'english': { 'short': 'en', 'mid': 'eng', 'long': 'English', 'orig': 'English'},
  'french': { 'short': 'fr', 'mid': 'fre', 'long': 'French', 'orig': ''},
  'russian': { 'short': 'ru', 'mid': 'rus', 'long': 'Russian', 'orig': ''},
  'spanish': { 'short': 'es', 'mid': 'spa', 'long': 'Spanish', 'orig': ''},
}

records_dict = {}
records = []

#for i in range(0,4441):
for i in range(0,200):
  base_url = 'https://s3.amazonaws.com/un-digital-library/unov/' + str(i) + '/'
  #metadata_dc = urlopen(base_url + 'dublin_core.xml')
  #metadata_undr = urlopen(base_url + 'metadata_undr.xml')
  #contents = urlopen(base_url + 'contents')

  dc_tree = ET.parse(urlopen(base_url + 'dublin_core.xml'))
  dc_root = dc_tree.getroot()
  undr_tree = ET.parse(urlopen(base_url + 'metadata_undr.xml'))
  undr_root = undr_tree.getroot()
  print(base_url)

  # Even if there are multiple symbols, let's just index by the first one.
  try:
    symbol = undr_root.find("dcvalue[@element='identifier'][@qualifier='symbol']").text
  except AttributeError:
    # We can't find a document symbol for the item; this happens for things that are older than the U.N., for obvious reasons.
    # Let's just grab the contents of the handle file
    symbol = urlopen(base_url + 'handle').readline().strip()
  print (symbol)

  duplicates = 0
  if symbol in records_dict:
    print("Merging record")
    duplicates += 1
  else:
    print("Making a new record")

  record = Record()

  for child in dc_root:
    if child.attrib['element'] == 'date' and child.attrib['qualifier'] == 'issued':
      record.add_field(
        Field(
          tag = '269',
          indicators = [' ',' '],
          subfields = [
            'a', child.text.replace("-","")[0:8]
          ]))

    if child.attrib['element'] == 'language' and child.attrib['qualifier'] == 'none':
      if record['041']:
        record['041']['a'] += languages[child.text.lower()]['mid']
      else:
        record.add_field(
          Field(
            tag = '041',
            indicators = [' ',' '],
            subfields = [
              'a', languages[child.text.lower()]['mid']
            ]))

    if child.attrib['element'] == 'title' and child.attrib['qualifier'] == 'none':
      if child.attrib['language'] == 'en':
        record.add_field(
          Field(
            tag = '245',
            indicators = ['1','0'],
            subfields = [
              'a', child.text
            ]))
      else:
        record.add_field(
          Field(
            tag = '246',
            indicators = [' ',' '],
            subfields = [
              'a', child.text
            ]))


  for child in undr_root:
    if child.attrib['element'] == 'identifier' and child.attrib['qualifier'] == 'symbol':
      record.add_field(
          Field(
            tag = '191',
            indicators = [' ',' '],
            subfields = [
              'a', child.text
            ]))

  records_dict[symbol] = marcxml.record_to_xml(record)
  #records.append(marcxml.record_to_xml(record)) 

print(duplicates)
