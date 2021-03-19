# Anime-dl

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
![GitHub](https://img.shields.io/github/license/Anon-Exploiter/anime-dl)
[![Contributors][contributors-shield]][contributors-url]
![GitHub closed issues](https://img.shields.io/github/issues-closed/Anon-Exploiter/anime-dl)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/cloudposse.svg?style=social&label=%40syed_umar)](https://twitter.com/syed__umar)

[contributors-shield]: https://img.shields.io/github/contributors/Anon-Exploiter/anime-dl.svg?style=flat-square
[contributors-url]: https://github.com/Anon-Exploiter/anime-dl/graphs/contributors
[issues-shield]: https://img.shields.io/github/issues/Anon-Exploiter/anime-dl.svg?style=flat-square
[issues-url]: https://github.com/Anon-Exploiter/anime-dl/issues

Python3 script to download subbed animes from 4anime & gogoanime.ai (the sites with best quality i.e. 1080p)

[![asciicast](https://asciinema.org/a/400635.svg)](https://asciinema.org/a/400635)

### Description

Anime-dl requires **Python3** and **aria2** (for working/parsing/downloading). ( ͡° ͜ʖ ͡°)

It automates everything, all you've to do is to pass whichever anime you want to download and it'll fetch all the **episodes**, their **DDLs**, create a new directory with anime as the name, use **aria2c** to download **2 episodes in parallel** by default. (customizable config with usage of `-p` arg) 

### Where do I get anime list?

**Anime list (4anime.to):** https://4anime.to/browse
**Anime list (gogoanime.ai):** https://gogoanime.ai/anime-list.html

### Requirements (to be installed)
- aria2
- python3
- python3-bs4
- python3-requests

### Tested On
- Ubuntu 18.04 LTS
- Pop! OS 20.04 LTS
- ~Windows~

### Installation
```bash
mkdir env && cd env
python3 -m venv . 
source bin/activate 
cd -
pip install -r requirements.txt

sudo apt-get update && sudo apt-get install -y aria2
```

### Usage

Downloading a series with (no and) five parallel processes
```
python3 anime-dl.py --url https://4anime.to/anime/mob-psycho-100
python3 anime-dl.py --url https://gogoanime.ai/category/mob-psycho-100 -p 5
```

Starting the series from a specific point (i.e. from 138th episode till end)
```
python3 anime-dl.py --url https://4anime.to/anime/black-clover -s 138
python3 anime-dl.py --url https://gogoanime.ai/category/black-clover-tv -p 5 -s 140
```

### Features
- Fetches information about the anime, title, desc, etc.
- Lists all episodes
- Fetches all episodes' direct download links
- Creates directory from the parsed episode details
- Downloads and places all the courses inside the anime (name) folder
- Start downloading from a specific episode

### Features (not-supported/todos)
- ~Continuing from a specific episode~ (completed)
- Ending on a specific episode
- Downloading only a specific episode

### Filing Bugs/Contribution
Feel free to file a issue or create a PR for that issue if you come across any.

### Sum screenshots pls
<img src="https://i.imgur.com/Sh0j6qV.png" />

### Changelog
| Changes                                                                                                                                   | Release                                             |
| ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Integrates downloading from gogoanime.ai in addition to 4anime.to                                                                         | 2.0 - 20-03-2021                                    |
| Fixes major bugs causing issues while downloading episodes from 4anime.to                                                                 | 1.0 - 10-03-2021                                    |
| Second release allowing user to start from a specific episode                                                                             | 0.2 - 23-09-2020                                    |
| Initial release only integrating downloading of anime episodes from google appspot application (-> Dies Irae fails)                       | 0.1 - 21-09-2020                                    |
