#!/usr/bin/python3

from bs4 import BeautifulSoup
import os
import requests
import concurrent.futures
import argparse
import re
import urllib.parse
import sys

def write(var = "!", text = "test"):
	print(f"[{var}] {text}")

def addArguments():
	parser 		= argparse.ArgumentParser(description='', usage=f'\r-------------------------------------------------\n\tAnime Downloader\n-------------------------------------------------\n\n[#] Usage: python3 anime-dl.py --url https://4anime.to/anime/jujutsu-kaisen-tv | https://gogoanime.ai/category/jujutsu-kaisen-tv')
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

def getEpisodesLinks(url):
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

def parseEpisodeLink(link):
	response 		= requests.get(link)

	while response.status_code != 200:
		response 		= requests.get(link)
	
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

def downloadEpisodes(command, directory):
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

def main():
	PPROCESSES 	= 10 		# Parsing Processes
	DPROCESSES 	= 1 		# Downloading Processes

	args, parser = addArguments()

	gogoAnime 		= ''
	fourAnime 		= ''

	if args.url:
		url 		= args.url
		commands 	= []

		if "gogoanime.ai" in url:
			gogoAnime 	= True

		else:
			fourAnime 	= True

		if args.p:
			DPROCESSES 	= int(args.p)

		if url and fourAnime:
			write(var = "#", text = "Fetching 4anime's anime ...\n")

			if args.p:
				write(var = "!", text = "4anime doesn't support multiple episodes download at once -- Please remove -p argument or try gogoanime")
				exit()
			
			episodes, directory = getEpisodesLinks(url)
			createCourseDirectory(directory)

			if args.start:
				startAt 	= int(args.start)
				episodes 	= episodes[startAt - 1:]

			# for eps in episodes.items():
			# 	parseEpisodeLink(eps[0], eps[1])

			with concurrent.futures.ProcessPoolExecutor(max_workers = PPROCESSES) as executor:
				for results in executor.map(parseEpisodeLink, episodes):
					commands.append(results)

			print()

			with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
				executor.map(downloadEpisodes, commands, [directory] * len(commands))

			print()

			write(var = "#", text = "Verfying anime episodes downloaded! ...")

			print()

			with concurrent.futures.ProcessPoolExecutor(max_workers = DPROCESSES) as executor:
				executor.map(downloadEpisodes, commands, [directory] * len(commands))

		elif url and gogoAnime:
			write(var = "#", text = "Fetching gogoanime's anime ...\n")

			goTitles 	= []
			goLinks 	= []

			if "-episode-" not in url:
				# For downloading whole series
				print("\n[%] Downloading series ...\n")
				
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

		else:
			parser.print_help()
			exit()

	else:
		parser.print_help()
		exit()

if __name__ == '__main__':
	main()
