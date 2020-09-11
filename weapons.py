from bs4 import BeautifulSoup
import time
import aiohttp
import asyncio
import csv
import time
from urllib.request import urlopen, Request


csv_header = ['Url', 'Name', 'Rarity', 'Damage', 'Weapon Type', 'Ammo Type', 'Season', 'Weapon Slot', 'Frame Type']
# '|' special character to be replaced later by the page id
base_url = 'https://www.light.gg/db/category/1?page=|&f=4%285%29%2C%2C%2C46%281360%3B1360%29'
single_base_url = 'https://www.light.gg/db/items/'
pages = 2



weapons = []
global_requests = 0
def _filter(text):
	return text.replace(' ', '').replace('\n', '').replace('\r', '')

async def get_page(session, page):
	global base_url
	url = base_url.replace('|', str(page))
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


		# in case webpage is empty
		if not info:
			raise Exception('Error on loading webpage')


		db_frame = soup.find('div', id='special-perks').find('img')['title']
		db_ammo_type = _filter(info[1].strong.text.capitalize())
		#print(info[2])
		db_season = _filter(info[2].strong.text.replace('Season ', ''))
		
		if 'Weapon' in info[3].text:
			li_text = _filter(info[3].text)

		elif 'Weapon' in info[5].text:
			li_text = _filter(info[5].text)

		elif 'Weapon' in info[7].text:
			li_text = _filter(info[7].text)
		else:
			raise Exception(f'Webscrape error on {url}')


		db_slot = li_text.replace('Weapon', '')
		global weapons
		weapons[weapon_pos] = weapons[weapon_pos] + [db_ammo_type, db_season, db_slot, db_frame]

		global global_requests
		global_requests += 1



# async request to trigger all the other requests
async def request_everything():
	async with aiohttp.ClientSession() as session:
		global weapons

		await asyncio.gather(*[asyncio.create_task(proccess_single(session, info[0], pos)) for pos, info in enumerate(weapons)])


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


	global csv_header
	weapons.insert(0, csv_header)

	with open('weapons.csv', 'w', newline='', encoding='utf-8') as file:
		writer = csv.writer(file)
		writer.writerows(weapons)
	print(f'total run time {time.time() - t_total}')

if __name__ == '__main__':
	main()

