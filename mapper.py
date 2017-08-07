#! /usr/bin/env python

import csv
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from urllib.error import HTTPError

languages = {
  'arabic': { 'short': 'ar', 'mid': 'ara', 'long': 'Arabic', 'orig': ''},
  'chinese': { 'short': 'zh', 'mid': 'chi', 'long': 'Chinese', 'orig': ''},
  'english': { 'short': 'en', 'mid': 'eng', 'long': 'English', 'orig': 'English'},
  'french': { 'short': 'fr', 'mid': 'fre', 'long': 'French', 'orig': ''},
  'russian': { 'short': 'ru', 'mid': 'rus', 'long': 'Russian', 'orig': ''},
  'spanish': { 'short': 'es', 'mid': 'spa', 'long': 'Spanish', 'orig': ''},
}

filesets = {}

for i in range(0,4441):
#for i in range(0,10):
  base_url = 'https://s3.amazonaws.com/un-digital-library/unov/' + str(i) + '/'
  undr_url = base_url + 'metadata_undr.xml'
  #print(undr_url)
  try:
    undr_tree = ET.parse(urlopen(undr_url))
  except HTTPError:
    undr_tree = ''

  try:
    undr_root = undr_tree.getroot()
  except AttributeError:
    undr_root = ''

  symbol = ''
  null_idx = 1

  try:
    symbol = undr_root.find("dcvalue[@element='identifier'][@qualifier='symbol']").text
  except AttributeError:
    # We can't find a document symbol for the item; this happens for things that are older than the U.N., even though we have managed
    # to assign them in other systems
    symbol = "Null-" + str(null_idx)
    null_idx += 1

  contents_url = base_url + 'contents'
  #print(contents_url)
  file_url = ''
  contents = urlopen(contents_url).read().decode()
  for c in contents.split('\n'):
    if "ORIGINAL" in c:
      for b in c.split('\t'):
        if ".pdf" in b:
          file_url = base_url + b
          #print(file_url)

  if symbol in filesets:
    # already exists, so let's append the contents file to the contents list
    filesets[symbol]['files'].append(file_url)
  else:
    # doesn't exist, so we create it
    filesets[symbol] = {}
    filesets[symbol]['files'] = [file_url]


out_file = open('file_map.dat','w+')
out_file.write(str(filesets))
out_file.close()
