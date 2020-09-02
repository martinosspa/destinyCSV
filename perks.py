from bs4 import BeautifulSoup
import time
import aiohttp
import asyncio
import csv
import time
from urllib.request import urlopen, Request

# example page
# https://www.light.gg/db/all/?page=1&f=10(barrel),-31
single_base_url = 'https://www.light.gg/db/items/'
base_url = 'https://www.light.gg/db/all/?page='
perks = []
url_pages = [5, 1, 1, 1, 1, 1, 1, 1, 1, 1]
urls = ['trait', 'barrel', 'guard', 'blade', 'magazine', 'bowstring', 'arrow', 'sight', 'battery', 'scope']

global_dict = {}
global_dict_counter = 0
global_perk_dict = {}

def _filter(text):
	return text.replace(' ', '').replace('\n', '').replace('\r', '')


def get_page(page, _type):
	global base_url
	url = f'{base_url}{page}&f=10({_type}),-31'
	# header for request
	header = {'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}

	# makes request
	req = Request(url, headers=header)
	resp = urlopen(req)

	# parser html to python
	soup = BeautifulSoup(resp, 'html.parser')
	_perks = soup.find_all('div', class_='item-row item-row-6')

	# finds items from the web list
	for perk in _perks:
		db_list = perk.find_all('div')

		db_type = db_list[-3].text.replace(' ', '').replace('\r', '').replace('\n', '')
		db_list = db_list[1].text.split('\n')

		db_link = perk.find_all('div')[0].a['href'].replace('/db/items/', '')
		db_name = db_list[1]
		db_desc = db_list[3].replace('  ', '').replace('\r', '').replace('\n', '')
		global perks
		if db_type == 'SparrowEngine' or db_type == 'SparrowMod':
			pass
		else:
			perks.append([db_link, db_name, db_type, db_desc])


#process single perk site
async def proccess_single(session, _id, perk_pos):
	global single_base_url
	async with session.get(f'{single_base_url}/{_id}') as response:
		text = await response.text()
		soup = BeautifulSoup(text, features='html.parser')
		t = soup.find('div', id='stat-container')
		individual_stats = []

		if t:
			tr_stats = t.find_all('td')
			stats = [_filter(stat.text) for stat in tr_stats if _filter(stat.text)]
			global global_dict_counter
			global global_perk_dict
			global_perk_dict[perk_pos] = {}
			for stat_pos in range(0, len(stats), 2):
				# if there isnt a column for the given stat create one
				if not stats[stat_pos] in global_dict:
					global_dict[stats[stat_pos]] = global_dict_counter
					global_dict_counter += 1

				perk_column_pos = global_dict[stats[stat_pos]]
				global_perk_dict[perk_pos][perk_column_pos] = stats[stat_pos+1]


# async request to trigger all the other requests
async def request_everything():
	async with aiohttp.ClientSession() as session:
		global perks
		await asyncio.gather(*[asyncio.create_task(proccess_single(session, _id[0], pos)) for pos, _id in enumerate(perks)])

		
def main():
	
	global urls
	global url_pages
	global perks
	total_length = len(urls)
	t_start = time.time()
	t_total = time.time()

	print('getting perk pages')
	for pos, trait_type in enumerate(urls):
		pages = 2 if url_pages[pos] == 1 else url_pages[pos]
		for page in range(1, pages):
			get_page(page, trait_type)

		print(f'{pos+1} / {total_length}')
	print(f'done in {time.time() - t_start}')


	print('getting perk stats')
	t_start = time.time()
	loop = asyncio.get_event_loop()
	loop.run_until_complete(request_everything())
	print(f'done in {time.time() - t_start}')


	# men mashese kan na ebreis ti kamnei touto : kamnei map ta dictionaries me position tou perk mazi me ta stat tou sto 2D list pou eshei ta perks me ta description tous
	print('finalizing csv')
	for perk_pos, perk_info in enumerate(perks):
		perk = perk_info[0]
		if perk_pos in global_perk_dict:
			perks[perk_pos] = perks[perk_pos][0:3] + [global_perk_dict[perk_pos][stat_id] if stat_id in global_perk_dict[perk_pos] else '' for stat_id in range(0, global_dict_counter)] + [perks[perk_pos][-1]]
		else:
			perks[perk_pos] = perks[perk_pos][0:3] + ['' for _ in range(0, global_dict_counter)] + [perks[perk_pos][-1]]

	stat_list = list(global_dict.keys())


	# Header at the top of the CSV, can be edited freely
	csv_header = ['Url', 'Name', 'Type'] + stat_list + ['Description']


	perks.insert(0, csv_header)
	with open('perks.csv', 'w', newline='', encoding='utf-8') as file:
		writer = csv.writer(file)
		writer.writerows(perks)
	print(f'total run time {time.time() - t_total}')

if __name__ == '__main__':
	main()

