from bs4 import BeautifulSoup
import time
import aiohttp
import asyncio
import csv
import time
from urllib.request import urlopen, Request

single_base_url = 'https://www.light.gg/db/items/'
base_url = 'https://www.light.gg/db/category/1/weapons/?page='
pages = 15
weapons = []
global_requests = 0
def _filter(text):
	return text.replace(' ', '').replace('\n', '').replace('\r', '')

async def get_page(session, page):
	global base_url
	url = f'{base_url}{page}'
	print(url)
	async with session.get(url) as response:
		text = await response.text()
		# parser html to python
		soup = BeautifulSoup(text, 'html.parser')
		divs = soup.find_all('div', class_='item-row item-row-6')

		# finds items from the web list
		for weapon in divs:
			#print(weapon.find_all('div'))
			t = weapon.find_all('div')
			
			db_link = t[1].a['href'].replace('/db/items/', '')
			db_rarity = _filter(t[4].text)
			db_type = _filter(t[-5].text)
			db_name = t[2].a.text
			db_energy = _filter(t[-6].img['title'].capitalize())
			global weapons
			weapons.append([db_link, db_name, db_rarity, db_energy, db_type])

#process single perk site
async def proccess_single(session, _id, weapon_pos):
	global single_base_url
	global global_requests
	url = f'{single_base_url}{_id}'
	async with session.get(url) as response:
		text = await response.text()
		soup = BeautifulSoup(text, features='html.parser')
		t = soup.find('ul', id='item-details')
		try:
			info = t.find_all('li')
		except:
			print(_id)
			print(url)

		db_damage_type = _filter(info[0].strong.text.capitalize())
		db_ammo_type = _filter(info[1].strong.text.capitalize())
		#print(info[2])
		db_season = _filter(info[2].strong.text.replace('Season ', ''))
		li_text = info[3].text
		if not ' Weapon' in li_text:
			li_text = info[4].text
			if not ' Weapon' in li_text:
				li_text = info[5].text

		db_slot = _filter(li_text.replace(' Weapon', ''))
		global weapons
		weapons[weapon_pos] = weapons[weapon_pos] + [db_damage_type, db_ammo_type, db_season, db_slot]
		global_requests += 1



# async request to trigger all the other requests
async def request_everything():
	async with aiohttp.ClientSession() as session:
		global weapons
		end = 0
		start = 0
		batch_pos = 0
		for batch_pos in range(100, len(weapons), 100):
			start = batch_pos - 100
			end = batch_pos
			await asyncio.gather(*[asyncio.create_task(proccess_single(session, info[0], pos+start)) for pos, info in enumerate(weapons[start:end])])
		start = batch_pos
		await asyncio.gather(*[asyncio.create_task(proccess_single(session, info[0], pos+start)) for pos, info in enumerate(weapons[end:])])
		print(f'done {batch_pos}')


async def request_pages():
	async with aiohttp.ClientSession() as session:
		global pages
		await asyncio.gather(*[asyncio.create_task(get_page(session, page)) for page in range(1, pages+1)])

def main():
	
	global url
	global pages
	t_start = time.time()
	t_total = time.time()

	print('getting perk pages')
	loop = asyncio.get_event_loop()
	loop.run_until_complete(request_pages())
	print(f'done in {time.time() - t_start}')

	
	print('getting weapon stats')
	t_start = time.time()
	loop.run_until_complete(request_everything())
	print(f'done in {time.time() - t_start}')
	'''


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
	csv_header = ['Url', 'Name', 'Rarity'] + stat_list + ['Description']
	'''


	#perks.insert(0, csv_header)

	with open('weapons.csv', 'w', newline='', encoding='utf-8') as file:
		writer = csv.writer(file)
		writer.writerows(weapons)
	print(f'total run time {time.time() - t_total}')

if __name__ == '__main__':
	main()

