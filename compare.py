"""
Takes metadata from Dspace and Metadat from DL and compare them
Return a list based with merged dispace metadata and information aobut availability in the digital library.
! Only compare with ECOSOC and GA documents in the dl. 
Disclaimer: Beginners script with loads of imperfection. To improve: query directly dl, instead of downoloading metadata.
"""

# Library to read and write csv files
import csv
import re
from bs4 import BeautifulSoup

def get_csv_row(file_name, header=True):
	"""
	Takes a csv file path, open it and returns a list of lists where nested lists correspond to csv rows. Remove the header by default. If the dataset
	does not have an header, the second argument need to ba added -> False
	Needs csv library.
	"""
	csv_rdr = csv.reader(open(file_name,'rb'))
	converted_list = [row for row in csv_rdr]
	if header is True:
		hd = converted_list[0]
		converted_list = converted_list[1:]
	else:
		hd = None
	return hd, converted_list

def transform_html_table(filepath, header=True):
	"""
	Takes an html file path (presumably from the digital library).
	Parse it and return a list of lists. 
	Needs Beautifuls oup4 library.
	"""
	html = open(filepath,'r')
	html_code = html.read()
	html_code = BeautifulSoup(html_code, 'lxml') # other parser html.parser
	rows = html_code.findAll('tr')
	if header is True:
		rows = rows[1:]
	converted_list = []
	for row in rows:
		cols = row.findAll('td')
		cols = [td.text.strip() for td in cols]
		converted_list.append(cols)
	return converted_list

def strip_symbol(symbol):
	symbol = re.sub('[^a-zA-Z0-9_*]', '', symbol)
	symbol = symbol.lower()
	symbol = symbol.strip()
	return symbol

def get_symbols_list(dataset,ind):
	""" 
	Takes a list of lists and index of the symbols in the nested list.
	Splits and strip the symbols to return a single list of symbols.
	"""
	symbols = [row[ind] for row in dataset]
	symbols = [v.split(';') for v in symbols]
	symbols_list = []
	for row in symbols:
		for symbol in row:
			symbols_list.append(strip_symbol(symbol))
	return symbols_list

def check_if_dl(dl_symbols, dataset,ind):
	"""
	Takes a list of symbol from the dl, compare it with the dataset[ind].
	Spit the dataset in 2, depending on whether a match is found or not.
	Return 2 distinct datasets.
	"""
	in_dl = [] 
	not_in_dl = []
	for row in dataset:
		symbols = row[ind]
		symbols = symbols.split('||')
		for symbol in symbols:
			s = strip_symbol(symbol)
			if  s in dl_symbols:
				in_dl.append(row)
				break
		else:
			not_in_dl.append(row)
	return in_dl, not_in_dl

def write_csv(dataset,filename):
	"""
	Takes a list of lists a filepath. Output a csv file where each nested list is a row.
	"""
	with open(filename,'wb') as csvfile:
		wrt = csv.writer(csvfile)
		wrt.writerows(dataset)

def split_by_language(data,ind):
	"""
	Takes a dataset and split it by anguage
	"""
	en = []
	fr = []
	es = []
	others = []
	for row in data:
		if row[ind] == 'French':
			fr.append(row)
		elif row[ind] == 'English':
			en.append(row)
		elif row[ind] == 'Spanish':
			es.append(row)
		else:
			others.append(row)
	return en, fr, es, others

def create_new_row(row):
	"""
	Create a new row, with particular metadata for each language.
	"""
	if row[9] == 'English':
		new_row = [row[20],row[19],row[3],row[2],row[4],row[10],
		None,None,None,row[0],None,None,None, row[5],None,None,None,
		row[6],None,None,None,row[15],None,None,None]
	elif row[9] == 'French':
		new_row =[row[20],row[19],row[3],row[2],row[4],None,row[12],None,None,None,row[0],None,None,None,row[5],None,None,None,row[6],None,None,None,row[16],None,None]
	elif row[9] == 'Spanish':
		new_row = [row[20],row[19],row[3],row[2],row[4],None,None,row[11],None,None,None,row[0],None,None,None,row[5],None,None,None,row[6],None,None,None,row[17],None]
	else:
		new_row = [row[20],row[19],row[3],row[2],row[4],None,None,None,row[13],None,None,None,row[0],None,None,None,row[5],None,None,None,row[6],None,None,None,row[18]]
	return new_row

def update_row(row,new_row):
	"""
	Update rows to include language metadata on an existing row.
	"""
	if row[9] == 'English':
		new_row[13]	= row[5]
		new_row[17]	= row[6]
		new_row[5]	= row[10]
		new_row[21]	= row[15]
		new_row[9]	= row[0]
	elif row[9] == 'French':
		new_row[14]	= row[5]
		new_row[18]	= row[6]
		new_row[6]	= row[12]
		new_row[22]	= row[16]
		new_row[10]	= row[0]
	elif row[9] == 'Spanish':
		new_row[15]	= row[5]
		new_row[19] = row[6]
		new_row[7]	= row[11]
		new_row[23]	= row[17]
		new_row[11]	= row[0]
	else:
		new_row[16]	= row[5]
		new_row[20]	= row[6]
		new_row[8]	= row[13]
		new_row[24]	= row[18]
		new_row[12]	= row[0]
	return new_row

def deduplicate(dataset):
	new_dataset = []
	symbols = []
	for row in dataset:
		if row[20] in symbols:
			for new_row in new_dataset:
				if row[20] == new_row[0]:
					new_row = update_row(row, new_row)
		else:
			symbols.append(row[20])
			new_dataset.append(create_new_row(row))
	return new_dataset

def merge_dataset(d1, d2, hd):
	"""
	Merge the 2 datasets, add headers and information aout dl availablility
	"""
	merged_data = []
	merged_data.append(hd)
	for row in d1:
		row.append('y')
		merged_data.append(row)
	for row in d2:
		row.append('n')
		merged_data.append(row)
	return merged_data



# Creates 2 list2 of list2, from html file (dl) and from csv file(dspace)
dl = transform_html_table('data/dl_a_e.html')
hd,ds = get_csv_row('data/ds_all.csv')
# Deduplicate Dspace data and store language metadata in specific fields
ds = deduplicate(ds)
# Creates a list of symbols from the dl file.
dl_symbols = get_symbols_list(dl,1)
# In each dataset add column to reflect the findings.
in_dl, not_dl = check_if_dl(dl_symbols,ds,0)

header = ["symbol","79","269","coverage","500","en_245","fr_245","es_245","ru_245","en_id","fr_id","es_id","ru_id","en_020","fr_020","es_020","ru_020","en_022","es_022","fr_022","ru_022","en_710","es_710","fr_710","ru_710"]

merged = merge_dataset(in_dl, not_dl, header)

write_csv(merged,'export/unov_ds_analyzed.csv')
