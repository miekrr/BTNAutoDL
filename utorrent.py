#!/usr/bin/python
import os
import sys
import win32gui
import win32process
import win32com.client

__utorrent_procees_name__ = "uTorrent.exe"
__shortcut_bosskey__ = "^%q" # CTRL + ALT + Q

shell = win32com.client.Dispatch("WScript.Shell")

def showUtorrent():
	if isUtorrentHidden():
		shell.SendKeys(__shortcut_bosskey__)


def hideUtorrent():
	if not isUtorrentHidden():
		shell.SendKeys(__shortcut_bosskey__)


def get_hwnds_for_pid (pid):
  def callback (hwnd, hwnds):
    if win32gui.IsWindowVisible (hwnd) and win32gui.IsWindowEnabled (hwnd):
      _, found_pid = win32process.GetWindowThreadProcessId (hwnd)
      if found_pid == pid:
        hwnds.append (hwnd)
    return True
    
  hwnds = []
  win32gui.EnumWindows (callback, hwnds)
  return hwnds


def isUtorrentHidden():
	hwnd = get_hwnds_for_pid(getUtorrentPid())
	try:
		winTxt = win32gui.GetWindowText(hwnd[0])
	except:
		winTxt = ""
	ret = False
	if not winTxt:
		ret = True
	#print("utorrent hidden: " + str(ret))
	return ret


def getUtorrentPid():
	pids = []
	processNames = []
	a = os.popen("tasklist").readlines()
	#print(a[10])
	for x in a:
		try:
			processNames.append((x[0:29]))
			pids.append(x[29:34])
		except:
			pass
	for idx in range(0, len(pids)):
		if(processNames[idx].strip() == __utorrent_procees_name__):
			return(int(pids[idx]))

	return None


def processArgs():
	if(len(sys.argv) == 2):
		selectFunction = {
			'showUtorrent': showUtorrent,
			'hideUtorrent': hideUtorrent
		}
		selectedFunction = selectFunction[sys.argv[1]]
		selectedFunction()
	else:
		print("Please provide only one function to be called!")


processArgs()
