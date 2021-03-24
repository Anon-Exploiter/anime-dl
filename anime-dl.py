#!/usr/bin/python3

from bs4 import BeautifulSoup
import os
import requests
import concurrent.futures
import argparse
import re
import urllib.parse
import sys
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def write(var = "!", text = "test"):
	print(f"[{var}] {text}")

def addArguments():
	parser 		= argparse.ArgumentParser(description='', usage=f'\r-------------------------------------------------\n\tAnime Downloader\n-------------------------------------------------\n\n[#] Usage: python3 anime-dl.py --url https://gogoanime.ai/category/jujutsu-kaisen-tv | https://4anime.to/anime/jujutsu-kaisen-tv')
	parser._optionals.title = "Basic Help"

	basicFuncs 	= parser.add_argument_group(f'Input required')
	basicFuncs.add_argument('-u', '--url', 			action="store", 	dest="url", 		default=False, 		help='URL of Anime to download')	
	basicFuncs.add_argument('-p', '--processes', 	action="store", 	dest="p", 			default=False, 		help='Parallel downloading processes')

	opts 		= parser.add_argument_group(f'Arguments')
	opts.add_argument('-s', '--start', 				action="store", 	dest="start", 		default=False, 		help='Where to start from? (i.e. from 95)')

	args = parser.parse_args()
	return(args, parser)

def createCourseDirectory(name):
	"""
	For creation of the course directory
	"""

	path 		= os.getcwd()
	courseDir	= os.path.join(path, name)

	if not(os.path.isdir(courseDir)):
		os.mkdir(courseDir)

def get4animeEpisodesLinks(url):
	returnData 			= []
	response 			= requests.get(url)

	if response.status_code == 200:
		responseText	= response.text
		changedResponse	= responseText.replace('title=""', 'title="episodes"')
		soup 			= BeautifulSoup(changedResponse, 'html.parser')

		title 			= soup.find('title').text
		description 	= soup.find('div', {'id': 'description-mob'}).text.replace('Description ', '').strip()

		links 			= soup.find_all('a', {'title': 'episodes'})
		count 			= len(links)

		print()
		write("*", f"Title: {title}")
		write("&", f"Total Episodes: {count}")
		write("$", f"Description: {description[:60]} ...")
		print()

		for atags in links:
			href 		= atags['href']
			returnData.append(href)

		return(returnData, title)

	else:
		write(var = "!", text = "There was a problem fetching the episodes")

def parse4animeEpisodeLink(link):
	response 		= requests.get(link)

	while response.status_code != 200:
		response 	= requests.get(link)
	
	responseText	= response.text
	soup 			= BeautifulSoup(responseText, 'html.parser')

	title 			= soup.find('title').text

	# They changed the implementation, and are changing the hostname of the subdomain in runtime using JS, files weren't being downloaded. 
	# Probably to trick scripts :P

	# Before: 	https://mountainoservoo002.animecdn.com/Black-Clover/Black-Clover-Episode-2-1080p.mp4
	# After: 	https://mountainoservo0002.animecdn.com/Black-Clover/Black-Clover-Episode-2-1080p.mp4

	# The replacement below fixes that issue and proceeds with downloading of files!

	ddl 			= soup.find('source')['src'].replace('mountainoservoo002', 'mountainoservo0002')

	write('*', f'{title} {ddl}')
	return(title, ddl)

def download4animeEpisodes(command, directory):
	title 		= command[0].replace(' ', '_')
	ddl 		= command[1]

	fileName 	= f"{directory}/{title}.mp4"

	if os.path.isfile(fileName) and not(os.path.isfile(f"{fileName}.aria2")):
		write(var="#", text=f'{fileName} already exists!')
		command = ""

	else:
		# Changing threads to 5 since the server returns error on 16 connections at once. Also, on 5 speed is better than 16, I think they limit your speed based on the connections you're making. 
		command 	= f"aria2c -s 10 -j 10 -x 5 --file-allocation=none -c -o '{fileName}' '{ddl}'"
		write(var="&", text=command)

	os.system(command)

def parseGogoAnimeAi(animeURL):
	epLinks 	= []
	response 	= requests.get(animeURL)

	# https://ajax.gogo-load.com/ajax/load-list-episode?ep_start=0&ep_end=22&id=9639&default_ep=0&alias=jujutsu-kaisen-tv
	# https://ajax.gogo-load.com/ajax/load-list-episode?ep_start=900&ep_end=965&id=171&default_ep=0&alias=one-piece

	# Can be reduced to:
	# https://ajax.gogo-load.com/ajax/load-list-episode?ep_start={starting}&ep_end={ending}&id={animeId}

	if response.status_code == 200:
		soup 		= BeautifulSoup(response.text, 'html.parser')
		animeId		= soup.find_all('input', {'type': 'hidden', 'id': 'movie_id', 'class': 'movie_id'})[0]['value']

		animeTitle 	= soup.find('h1').text
		description = soup.find_all('p', {'class': 'type'})[1].text.replace('Plot Summary: ', '')

		# Will later on take {starting} arg as user input
		starting 	= 0

		# Big value of {ending} to get all episodes links in one go!
		ending 		= 10000

		# Episodes link
		episodes	= f'https://ajax.gogo-load.com/ajax/load-list-episode?ep_start={starting}&ep_end={ending}&id={animeId}'

		# Fetching tags
		response 	= requests.get(episodes).text
		htmlTags 	= BeautifulSoup(response, 'html.parser')
		aTags 		= htmlTags.find_all('a')

		for tags in aTags:
			links 	= 'https://gogoanime.ai' + tags['href'].replace(' ', '')
			epLinks.append(links)

		# Episode links
		epLinks 	= epLinks[::-1]

		write("*", f"Title: {animeTitle}")
		write("&", f"Total Episodes: {len(epLinks)}")
		write("$", f"Description: {description[:60]} ...")

		return(epLinks)

def parseGogoAnimeDLinks(link):
	downloadLink 	= ""
	response 		= requests.get(link).text

	soup 			= BeautifulSoup(response, 'html.parser')
	liTag 			= soup.find('li', {'class': 'dowloads'})

	for links in liTag:
		dlLink 		= links['href']

	dResponse 		= requests.get(dlLink).text
	linksRegex 		= r'href="(.*?)" download'

	matches 		= re.findall(linksRegex, dResponse)[::-1]
	downloadLink 	= matches[0]

	for links in matches:
		if "storage.googleapis.com" in links:
			downloadLink = links

	dlLink 			= downloadLink.replace('&amp;', '&')

	write('*', f'{link} {dlLink}')
	return(link, dlLink)

def downloadGogoEpisodes(title, ddl):
	title 		= title.split("/")[::-1][0]
	directory 	= title.split('-episode-')[0]
	createCourseDirectory(directory)

	# print(title, directory, ddl)

	fileName 	= f"{directory}/{title}.mp4"

	if os.path.isfile(fileName) and not(os.path.isfile(f"{fileName}.aria2")):
		write(var="#", text=f'{fileName} already exists!')
		command = ""

	else:
		command 	= f"aria2c -s 10 -j 10 -x 16 --file-allocation=none -c -o '{fileName}' '{ddl}'"
		write(var="$", text=command)

	os.system(command)

def parseGogoanimeBeSeries(url):
	epLinks 	= []
	response 	= requests.get(url)

	if response.status_code == 200:
		soup 		= BeautifulSoup(response.text, 'html.parser')
		animeLinks	= soup.find_all('a', {'class': 'nav-link btn btn-sm btn-secondary eps-item'})

		for tags in animeLinks:
			links 	= tags['href']
			epLinks.append(links)

		animeTitle 	= soup.find('h1').text
		description = soup.find_all('div', {'class': 'description'})[0].text

		write("*", f"Title: {animeTitle}")
		write("&", f"Total Episodes: {len(epLinks)}")
		write("$", f"Description: {description[:60]} ...")

		return(epLinks)

	else:
		print(f"[!] There are some issues parsing the link ({url})")

def parseGogoAnimeBeDLinks(link):
	downloadLink 	= ''
	response 		= requests.get(link).text

	soup 			= BeautifulSoup(response, 'html.parser')
	dlLink 			= soup.find_all('a', {'class': 'nav-link btn btn-sm btn-secondary link-item'})[0]['data-embed']

	episodeId 		= re.findall(r'.*/e/(.*?)\?domain=.*', dlLink)[0]
	# print(episodeId)

	dlLink 			= f"https://vidstream.pro/info/{episodeId}?domain=gogoanime.be&skey=db04c5540929bebd456b9b16643fc436"
	
	dlLinkResponse 	= requests.get(dlLink,
		headers 	= {
			'Referer': 'https://gogoanime.be/'
		},
		# proxies 	= {
		# 	'http': '127.0.0.1:8080',
		# 	'https': '127.0.0.1:8080',
		# },
		# verify 		= False
	)

	if dlLinkResponse.status_code == 200:
		jsonData 		= json.loads(dlLinkResponse.text)
		# print(jsonData)

		downloadLink = jsonData['media']['sources'][0]['file']

		if ".m3u8" in downloadLink:
			ddl 	= jsonData['media']['download']
			token 	= BeautifulSoup(requests.get(ddl).text, 'html.parser').find('input', {'type': 'hidden', 'name': 'token'})['value']
			
			resp 	= requests.post(ddl,
				data 		= {
					'token': token
				},
				headers 	= {
					'Referer': ddl
				},
				allow_redirects = False,
				# proxies 	= {
				# 	'http': '127.0.0.1:8080',
				# 	'https': '127.0.0.1:8080',
				# },
				# verify 			= False,
			)

			soup 			= BeautifulSoup(resp.text, 'html.parser')
			downloadLink 	= soup.find('a')['href']
			# print(downloadLink)

		write('*', f'{episodeId} | {link} | {downloadLink[:120]} ...')
		return(link, downloadLink)

	else:
		print()
		write('!', f'Episode not found on server | {episodeId} | {link} | Please download this manually! >_< ...')
		print()
		return('', '')

def downloadGogoAnimeBeEpisodes(title, ddl, singleEpisode=False):
	title 		= title.split("/")[::-1][1]
	gtitle 		= " ".join(title.split('-episode-')[0].split("-")[:-1]).capitalize()
	directory 	= gtitle.split('-episode-')[0]

	print(title, gtitle, directory)

	createCourseDirectory(directory)

	fileName 	= f"{directory}/{title}.mp4"

	if os.path.isfile(fileName) and not(os.path.isfile(f"{fileName}.aria2")):
		write(var="#", text=f'{fileName} already exists!')
		command = ""

	else:
		command 	= f"aria2c -s 10 -j 10 -x 16 --file-allocation=none -c -o '{fileName}' '{ddl}'"
		write(var="$", text=command)

	os.system(command)

def main():
	PPROCESSES 	= 10 		# Parsing Processes
	DPROCESSES 	= 1 		# Downloading Processes

	args, parser = addArguments()

	gogoAnimeAi = ''
	gogoAnimeBe = ''
	fourAnime 	= ''

	if args.url:
		url 		= args.url
		commands 	= []

		if "gogoanime.ai" in url:
			gogoAnimeAi = True

		elif "gogoanime.be" in url:
			gogoAnimeBe	= True

		else:
			fourAnime 	= True

		###

		if args.p:
			DPROCESSES 	= int(args.p)

		if fourAnime:
			write(var = "#", text = "Fetching 4anime's anime ...\n")

			if args.p:
				write(var = "!", text = "4anime doesn't support multiple episodes download at once -- Please remove -p argument or try gogoanime")
				exit()
			
			episodes, directory = get4animeEpisodesLinks(url)
			createCourseDirectory(directory)

			if args.start:
				startAt 	= int(args.start)
				episodes 	= episodes[startAt - 1:]

			# for eps in episodes.items():
			# 	parse4animeEpisodeLink(eps[0], eps[1])

			with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
				for results in executor.map(parse4animeEpisodeLink, episodes):
					commands.append(results)

			print()

			with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
				executor.map(download4animeEpisodes, commands, [directory] * len(commands))

			print()

			write(var = "#", text = "Verfying anime episodes downloaded! ...")

			print()

			with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
				executor.map(download4animeEpisodes, commands, [directory] * len(commands))

		elif gogoAnimeAi:
			write(var = "#", text = "Fetching gogoanime's anime ...\n")

			goTitles 	= []
			goLinks 	= []

			if "-episode-" not in url:
				# For downloading whole series
				print("[%] Downloading series ...\n")
				
				epLinks 	= parseGogoAnimeAi(url)

				print()

				if args.start:
					startAt 	= int(args.start)
					epLinks 	= epLinks[startAt - 1:]

				# for links in epLinks:
				# 	parseGogoAnimeLinks(links)

				with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
					for results in executor.map(parseGogoAnimeDLinks, epLinks):
						goTitles.append(results[0])
						goLinks.append(results[1])

				print()

				with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
					executor.map(downloadGogoEpisodes, goTitles, goLinks)

			else:
				# For downloading a single episode
				print("[%] Downloading single episode ...\n")
				
				with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
					for results in executor.map(parseGogoAnimeDLinks, [url]):
						goTitles.append(results[0])
						goLinks.append(results[1])

				print()

				with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
					executor.map(downloadGogoEpisodes, goTitles, goLinks)

		elif gogoAnimeBe:
			write(var = "#", text = "Fetching Gogoanime.be's Anime ...\n")

			goTitles 	= []
			goLinks 	= []

			if "-episode-" not in url:
				# For downloading whole series
				print("[%] Downloading series ...\n")
				
				epLinks 	= parseGogoanimeBeSeries(url)

				print()

				if args.start:
					startAt 	= int(args.start)
					epLinks 	= epLinks[startAt - 1:]

				# for links in epLinks:
				# 	parseGogoAnimeBeDLinks(links)

				with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
					for results in executor.map(parseGogoAnimeBeDLinks, epLinks):
						goTitles.append(results[0])
						goLinks.append(results[1])

				print()

				with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
					executor.map(downloadGogoAnimeBeEpisodes, goTitles, goLinks)
			
			else:
				# For downloading a single episode
				print("[%] Downloading single episode ...\n")

				with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
					for results in executor.map(parseGogoAnimeBeDLinks, [url]):
						goTitles.append(results[0])
						goLinks.append(results[1])

				print()

				with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
					executor.map(downloadGogoAnimeBeEpisodes, goTitles, goLinks)

		else:
			parser.print_help()
			exit()

	else:
		parser.print_help()
		exit()

if __name__ == '__main__':
	main()
