#!/usr/bin/python

import configparser
import hexchat
import urllib.request
import sys
import subprocess
import os
import re
import logging

LOG_FILENAME = hexchat.get_info('configdir') + '\\addons\\btn-auto.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.disable(logging.DEBUG)

__module_name__ = "BTN Auto-DL"
__module_version__ = "1.0"
__module_description__ = "Download torrents that match your filters"
print(__module_name__ + " Loaded!")

filter_ini = hexchat.get_info('configdir') + "\\addons\\filters.ini"
lang_ini = hexchat.get_info('configdir') + "\\addons\\languages.ini"
irc = {
	"server":"paragon.irc.broadcasthe.net",
	"channel":"#BTN-WhatAuto"
}

url_info = {
	"url":"https://broadcasthe.net/torrents.php?action=download&id="
}

LOG_TAB = "BTN-AutoDL"

ADDONS_DIR = hexchat.get_info('configdir') + "\\addons\\"


def showUtorrent():
	processCmd = ["python", ADDONS_DIR + "utorrent.py", "showUtorrent"]
	status = subprocess.call(processCmd)


def hideUtorrent():
	subprocess.call(["python", ADDONS_DIR + "utorrent.py", "hideUtorrent"])


def findLogTab():
	context = hexchat.find_context(channel=LOG_TAB)
	if context == None: # Create a new one in the background
		newtofront = hexchat.get_prefs('gui_tab_newtofront')
		hexchat.command('set -quiet gui_tab_newtofront 0')
		hexchat.command('newserver -noconnect {0}'.format(LOG_TAB))
		hexchat.command('set -quiet gui_tab_newtofront {}'.format(newtofront))
		return hexchat.find_context(channel=LOG_TAB)
	else:
		return context	


def writeToLog(download_torrent,releaseName):
	log_context = findLogTab()
	if download_torrent == True:
		log = "\002\00303[New Download]\00399 " + releaseName + "\002"
		log_context.prnt(log)
	elif download_torrent == "force":
		log = "\002\00303[Forced Download]\00399 " + releaseName + "\002"
		log_context.prnt(log)
	log_context.command('gui color 3')


def dlTorrent(config, series, name):
	torrent_url = url_info["url"] + url_info["id"] + "&authkey=" + config['DirectUrl']['authkey'] + "&torrent_pass=" + config['DirectUrl']['passkey']
	saved_torrent_file = config['Directories']['torrent'] + "\\" + name + ".torrent"

	urllib.request.urlretrieve(torrent_url, saved_torrent_file)

	if config.has_option("General","client"):
		if config["General"]["client"] == "deluge":
			saveTo = series["save-to"].replace('\\', '/')
			delugeCmd = "\"" + config['Directories']['deluge'] + "\\deluge-console.exe\"" + " \"add -p '" + saveTo + "' '" + saved_torrent_file + "'\""
			subprocess.call(delugeCmd)
		elif config["General"]["client"] == "utorrent":
			utorrentCmd = "\"" + config['Directories']['utorrent'] + "\\utorrent.exe\"" + " /MINIMIZED /DIRECTORY \"" + series['save-to'] + "\" \"" + saved_torrent_file + "\""
			showUtorrent()
			subprocess.call(utorrentCmd)
			hideUtorrent()
	return


def checkSeason(config,announceFilters):
	if announceFilters['title'].endswith("E01") == True:
		series = config[announceFilters['series']]
		dirSplit = series['save-to'].rsplit("\\",1)
		newFolder = ""
		if announceFilters['resolution'] == "SD":
			newFolder = re.sub(r"E01.*"+announceFilters["source"],"."+announceFilters["source"],announceFilters['release-name'])
		else:
			newFolder = re.sub(r"E01.*"+announceFilters["resolution"],"."+announceFilters["resolution"],announceFilters['release-name'])

		if announceFilters['scene'] == "Yes":
			newFolder = re.sub(r"[^-]*$","BTN",newFolder)

		newFolder = dirSplit[0] + "\\" + newFolder

		config = configparser.RawConfigParser()

		series = str(announceFilters['series'])
		config.read(filter_ini)
		config.set(series,"save-to",newFolder)
		with open(filter_ini,"w") as configfile:
			config.write(configfile)
		subprocess.Popen("mkdir \"" + newFolder + "\"", shell=True)
	return


def checkFilters(config,filters,announceFilters,download_torrent):
	for key,value in announceFilters.items():
		if config.has_option(filters, key):
			options = config[filters][key].split(",")
			download_torrent = True
			for opt in options:
				if key == "except-tags":
					matches = re.search('(?<!^)'+opt+'(?!$)',announceFilters['release-name'],re.IGNORECASE)
					if matches:
						download_torrent = False
						break
				elif key == "release-group":
					if announceFilters['release-name'].endswith(opt):
						download_torrent = True
						break
					else:
						download_torrent = False
				elif key == "language":
					languageList = configparser.ConfigParser()
					languageList.read(lang_ini)	
					ID = re.search("(\d+)$",announceFilters['language']).group(0)
					if languageList["Languages"][ID] == opt:
						download_torrent = True
						break
					else:
						download_torrent = False
				elif opt == value:
					download_torrent = True
					break
				else:
					download_torrent = False
			if download_torrent == False:
				return download_torrent
	return download_torrent


def readFilters(announceFilters):
	config = configparser.ConfigParser()
	config.read(filter_ini)	

	seriesName = announceFilters['series']
	download_torrent = False
	'''
	if announceFilters["release-type"] != "Episode":
		return download_torrent
	'''
	if config.has_section(seriesName):
		series = config[seriesName]

		if config.has_option(seriesName, 'enabled'):
			if series['enabled'] == "No":
				return
		
		download_torrent = True
		if config.has_option(seriesName,'filter'):
			download_torrent = checkFilters(config,"filter " + series['filter'],announceFilters,download_torrent)
		
		download_torrent = checkFilters(config,announceFilters['series'],announceFilters,download_torrent)

		if download_torrent == True:
			if config.has_option("General","new-season-folder") and config["General"]['new-season-folder'] == "Yes":
				checkSeason(config,announceFilters)

			dlTorrent(config,series,announceFilters['release-name'])

			if config.has_option("General","download-log") and config["General"]['download-log'] == "Yes":
				writeToLog(download_torrent,announceFilters['release-name'])


def parseAnnounce(announce):
	announce = announce.split(" | ")
	url_info["id"] = announce[10]
	del announce[10]
	
	filterTitles = "series","title","release-type","year","container","codec","source","resolution","scene","fast-torrent","uploader","language","release-name","except-tags","release-group"
	i = 0
	announceFilters = {}
	for t in filterTitles:
		if i < len(announce):
			announceFilters[t] = announce[i]
			i += 1
		else:
			announceFilters[t] = ""
	return readFilters(announceFilters)


def prepareDownload(word, mode):
	logging.debug("word = %s", word);
	logging.debug("mode = %s", mode);
	announce = word.split(" | ")
	downloadStatus = parseAnnounce(word)
	config = configparser.ConfigParser()
	config.read(filter_ini)
	try:
		series = config[announce[0]]
	except:
		return
	logging.debug("downloadStatus: %s", str(downloadStatus))
	if(downloadStatus == True):
		dlTorrent(config, series, announce[0])
	writeToLog(mode, word)


def checkChannel(word,word_eol,userdata):
	if hexchat.get_info('channel') == irc["channel"]:
		prepareDownload(word[1], "channel")


def checkCommand(word,word_eol,userdata):
	announce = word[2].split(" | ")

	if word[1] == "download":
		prepareDownload(word[2], "force")

	return hexchat.EAT_ALL


findLogTab()

hexchat.hook_command("AUTODL", checkCommand)
hexchat.hook_print("Channel Message", checkChannel)

