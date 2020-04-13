# -*- coding: utf-8 -*-
# use python3

import os, sys, re, requests, time, urllib.request
import unicodecsv as csv
from bs4 import BeautifulSoup


#functions
def ensure_dir(file_path):
	directory = os.path.dirname(file_path)
	if not os.path.exists(directory):
		os.makedirs(directory)

def download_page(url, path):
	if os.path.exists(path) and os.path.isfile(path):
		return False #time.sleep(0.01)
	else:
		urllib.request.urlretrieve(url,path)
		time.sleep(0.5);
		return True

def map_array(data, mapping): # data 2d (header, item); mapping 1d (header)
	output = ['' for i in range(len(mapping))]
	head_index = []
	size_index = []
	step_head = ''
	step_index = 0
	for i, item in enumerate(data):
		step_head = item[0]
		if head_index.count(step_head) <= 0:
			head_index.append(step_head)
			size_index.append(0)
		step_index = head_index.index(step_head)
		size_index[step_index] += 1
		next_mapping = get_array_mapping(head_index[step_index],size_index[step_index],mapping)
		if next_mapping >= 0:
			next_item = item[1].encode("utf8")
			output[next_mapping] = next_item.decode('utf8')
	return output

def get_array_mapping(header, nth, mapping_array):
	head_size = 0
	for i, item in enumerate(mapping_array):
		if item == header:
			head_size += 1
		if head_size == nth:
			return i
	return -1


# settings
VERSION = 0.1
DL_DIR = './pages/'
DL_DIR_CAT = DL_DIR+'cat/'
DL_DIR_YOJI = DL_DIR+'word/'
DL_TEXT = 'Downloading...'
tab_txt = '  '
yoji_txt = 'Word '
yoji_str = ''
cat_txt = 'Cat '
cat_str = ''
OUT_RAW = True
OUT_FILE = 'yojijukugo.csv'
IN_KANKEN = True # limit to kanken-related yojijukugo


# Hello
print('Jiten Online Yojijukugo Scraper v'+str(VERSION))

def download_yojijukugo():
	print(DL_TEXT)

	# setup soup from url
	url = 'https://yoji.jitenon.jp/sp/'
	response = requests.get(url)
	soup = BeautifulSoup(response.text, "html.parser")

	# download all kanken level pages
	cats = soup.findAll('a', href = re.compile(r'https://yoji\.jitenon\.jp/sp/cat/kyu.*\.html'))
	cat_cnt = 0
	cat_len = len(str(len(cats)))*2+1
	ensure_dir(DL_DIR_CAT)
	for link in cats:
		cat_cnt += 1
		cat_str = tab_txt+cat_txt+(str(cat_cnt)+'/'+str(len(cats)))#.rjust(cat_len)
		url = link['href']
		dl_url = link.get('href')
		dl_file = DL_DIR+url[url.find('/cat/')+1:]
		print(cat_str,end="\r")
		download_page(dl_url, dl_file)
	print((cat_str+' DONE').ljust(cat_len+len(tab_txt+cat_str)))

	# cycle through cat pages
	cats = [f for f in os.listdir(DL_DIR_CAT) if os.path.isfile(os.path.join(DL_DIR_CAT, f))]
	yoji_cnt = 0
	cat_cnt = 0
	cat_len = len(str(len(cats)))*2+1
	total_links = 0
	for cat in cats:
		cat_cnt += 1
		cat_str = cat_txt+(str(cat_cnt)+'/'+str(len(cats)))#.rjust(cat_len)
		soup = BeautifulSoup(open(DL_DIR_CAT+cat, encoding="utf8"), "html.parser")
		links = soup.findAll('a', href = re.compile(r'https://yoji\.jitenon\.jp/sp/yoji.*/.*\.html'))
		total_links += len(links)
		yoji_len = len(str(total_links))*2+1;
		#print(yoji_txt+str(len(links)).rjust(yoji_len),end="\r")
		# download yoji pages
		for link in links:
			yoji_cnt += 1
			yoji_str = yoji_txt+(str(yoji_cnt)+'/'+str(total_links))#.rjust(yoji_len)
			url = link['href']
			dl_url = link.get('href')
			dl_file = DL_DIR_YOJI+url[url.find('/sp/yoji')+4:].replace('/','-')
			print(tab_txt+yoji_str+' ('+cat_str+')',end="\r")
			ensure_dir(dl_file)
			download_page(dl_url, dl_file)
	print((tab_txt+yoji_str+' DONE').ljust(yoji_len+len(tab_txt+yoji_str+cat_str)))

def process_yojijukugo():
	print('Processing...')
	head_index = []
	size_index = []
	step_head = ''
	step_index = 0

	# data pass 1 - gather information
	pages = [f for f in os.listdir(DL_DIR_YOJI) if os.path.isfile(os.path.join(DL_DIR_YOJI, f))]
	data = [[] for i in range(len(pages))]
	#data = [[] for i in range(100)]
	step_size = 0
	page_str = ''
	page_len = 0
	for i, page in enumerate(pages):
		# if i>=100:
		# 	break
		page_str = tab_txt+'Reading page '+str(i+1)
		page_len = len(page_str) if len(page_str) > page_len else page_len
		print(page_str, end="\r")
		soup = BeautifulSoup(open(DL_DIR_YOJI+page, encoding="utf8"), "html.parser")
		#soup.decompose()
		items = soup.find('table', class_='yojimain').findAll('tr')
		for item in items:
			row_head = item.find('th')
			row_data = item.find('td')
			row_data = ''.join([str(x) for x in row_data.contents]).encode('utf8')
			if row_head != None:
				step_head = row_head.string.encode('utf8')
				if head_index.count(step_head) <= 0:
					head_index.append(step_head)
					size_index.append(0)
				step_index = head_index.index(step_head)
				step_size = 1 if not row_head.has_attr('rowspan') else int(row_head['rowspan'])
				size_index[step_index] = step_size if size_index[step_index] < step_size else size_index[step_index]
			data[i].append([step_head.decode('utf8'),row_data.decode('utf8')])
	print((tab_txt+'Pages analysed.').ljust(page_len))

	# data pass 2 - output csv
	output = csv.writer(open(OUT_FILE,'wb'), encoding='utf8')
	header_row = []
	for i, hd in enumerate(head_index):
		header_row += [hd.decode('utf8')] * size_index[i]
	output.writerow(header_row)
	for item in data:
		output.writerow(map_array(item, header_row))
	print(tab_txt+'Data saved to '+OUT_FILE)

download_yojijukugo()
process_yojijukugo()