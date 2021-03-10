#!/usr/bin/python3

from bs4 import BeautifulSoup
import os
import requests
import concurrent.futures
import argparse

def write(var = "!", text = "test"):
	print(f"[{var}] {text}")

def addArguments():
	parser 		= argparse.ArgumentParser(description='', usage=f'\r-------------------------------------------------\n\t4anime.to downloader\n-------------------------------------------------\n\n[#] Usage: python3 4anime.to --url https://4anime.to/anime/mob-psycho-100')
	parser._optionals.title = "Basic Help"

	basicFuncs 	= parser.add_argument_group(f'Input required')
	basicFuncs.add_argument('-u', '--url', 			action="store", 	dest="url", 		default=False, 		help='URL of Anime to download')	
	# basicFuncs.add_argument('-p', '--processes', 	action="store", 	dest="p", 			default=False, 		help='Parallel downloading processes')	

	opts 		= parser.add_argument_group(f'Arguments')
	opts.add_argument('-s', '--start', 				action="store", 	dest="start", 		default=False, 		help='Where to start from? (i.e. from 100)')

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

def checkAnimeURL(animeURL):
	response 	= requests.get(animeURL)
	
	if "/language/" in response.text:
		return (True, response)
	return False

def getEpisodesLinks(response):
	returnData 			= []

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
		write("&", f"Episodes: {count}")
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

	print(title, ddl)
	return(title, ddl)

def downloadEpisodes(command, directory):
	title 		= command[0].replace(' ', '_')
	ddl 		= command[1]

	fileName 	= f"{directory}/{title}.mp4"

	if os.path.isfile(fileName) and not(os.path.isfile(f"{fileName}.aria2")):
		print(f'[#] {fileName} already exists!')
		command = ""

	else:
		# Changing threads to 5 since the server returns error on 16 connections at once. Also, on 5 speed is better than 16, I think they limit your speed based on the connections you're making. 
		command 	= f"aria2c -s 10 -j 10 -x 5 --file-allocation=none -c -o '{fileName}' '{ddl}'"
		print(command)

	os.system(command)

def main():
	PPROCESSES 	= 10 		# Parsing Processes
	DPROCESSES 	= 1 		# Downloading Processes

	args, parser = addArguments()

	if args.url:
		url 		= args.url
		bar 		= "-" * 70
		commands 	= []

		# if args.p:
		# 	DPROCESSES 	= int(args.p)

		legitURL 	= checkAnimeURL(url)

		if legitURL[0]:
			write(var = "#", text = "Fetching anime ...")
			
			episodes, directory = getEpisodesLinks(legitURL[1])
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

		else:
			write(var = "!", text = "The anime doesn't exist or wrong url submitted!")

	else:
		parser.print_help()
		exit()

if __name__ == '__main__':
	main()
