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

# Let's grab authority codes for 650 and 651 fields.
# URL pattern = https://digitallibrary.un.org/search?ln=en&cc=Thesaurus&p=150__a%3A<term>&f=&rm=wrd&ln=en&fti=0&sf=&so=d&rg=10&sc=0&c=Thesaurus&c=&of=xm

a650s = {}
a650 = open('auth_650.dat','r')
for a in a650:
  lookup = a.replace(" ","+").strip()
  lookup_url = 'https://digitallibrary.un.org/search?ln=en&cc=Thesaurus&p=150__a%3A"' + lookup + '"&f=&rm=wrd&ln=en&fti=0&sf=&so=d&rg=10&sc=0&c=Thesaurus&c=&of=xm'
  print(lookup_url)
  xml_tree = ET.parse(urlopen(lookup_url, context=ctx))
  xml_root = xml_tree.getroot()[0]
  ns = {'marc':'http://www.loc.gov/MARC21/slim'}
  # There should be at least one. We are looking for an exact match...
  auth_records = xml_root.findall("marc:datafield[@tag='035']/marc:subfield[@code='a']", ns)
  for auth_record in auth_records:
    if 'DHLAUTH' in auth_record.text:
      a650s[a.strip()] = auth_record.text

out_file = open('a650.dat', 'w+')
out_file.write(str(a650s))
out_file.close()

# Completely unsurprisingly, 651 is different.
a651s = {}
a651 = open('auth_651.dat','r')
for a in a651:
  lookup = a.replace(" ","+").strip()
  lookup_url = 'https://digitallibrary.un.org/search?ln=en&cc=Thesaurus&p=1519_a%3A"' + lookup + '"&f=&rm=wrd&ln=en&fti=0&sf=&so=d&rg=10&sc=0&c=Thesaurus&c=&of=xm'
  print(lookup_url)
  xml_tree = ET.parse(urlopen(lookup_url, context=ctx))
  try:
    xml_root = xml_tree.getroot()[0]
  except IndexError:
    lookup_url = 'https://digitallibrary.un.org/search?ln=en&cc=Thesaurus&p=150__a%3A"' + lookup + '"&f=&rm=wrd&ln=en&fti=0&sf=&so=d&rg=10&sc=0&c=Thesaurus&c=&of=xm'
    print("Couldn't find that one, let's see if it's in 150 instead.")
    print(lookup_url)
    xml_tree = ET.parse(urlopen(lookup_url, context=ctx))
    xml_root = xml_tree.getroot()[0]
  ns = {'marc':'http://www.loc.gov/MARC21/slim'}
  # There should be at least one. We are looking for an exact match...
  auth_records = xml_root.findall("marc:datafield[@tag='035']/marc:subfield[@code='a']", ns)
  for auth_record in auth_records:
    if 'DHLAUTH' in auth_record.text:
      a651s[a.strip()] = auth_record.text

out_file = open('a651.dat','w+')
out_file.write(str(a651s))
out_file.close()
