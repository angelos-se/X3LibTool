#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Original Author: Angelos http://www.head-fi.org/u/395616/angelosc
# 2014 April
#
import os, sys, subprocess, sqlite3, unicodedata, eyed3

def SubStringAfterKey(string, key):
	return string[string.find(key)+len(key):]
def SubStringBeforeKey(string, key):
	return string[:string.find(key)]
def PathTransform(path):
	return "b:\\"+path.replace("/", "\\")
    
def M4Ainfo(file):
	MediaInfo = {'Title':'', 'Artist':'', 'Album':'', 'Genre':''}
	try:
		MediaInfo['Path'] = SubStringAfterKey(file, CWD)
		output = subprocess.check_output(['AtomicParsley', file, '-t'])
		for line in output.split('\n'):
			if   "©nam" in line: MediaInfo['Title'] = SubStringAfterKey(line, "contains: ").strip().decode("utf-8")
			elif "©ART" in line: MediaInfo['Artist'] = SubStringAfterKey(line, "contains: ").strip().decode("utf-8")
			elif "©alb" in line: MediaInfo['Album'] = SubStringAfterKey(line, "contains: ").strip().decode("utf-8")
			elif "©gen" in line: MediaInfo['Genre'] = SubStringAfterKey(line, "contains: ").strip().decode("utf-8")
			elif "trkn" in line:
				MediaInfo['TrackN'] = SubStringAfterKey(line, "contains: ").strip()
				if " of" in MediaInfo['TrackN']: MediaInfo['TrackN'] = SubStringBeforeKey(SubStringAfterKey(line, "contains: "), " of").strip()
			elif "disk" in line:
				MediaInfo['DiscN'] = SubStringAfterKey(line, "contains: ").strip()
				if " of" in MediaInfo['DiscN']: MediaInfo['DiscN'] = SubStringBeforeKey(SubStringAfterKey(line, "contains: "), " of").strip()
		if len(MediaInfo.get('Title', ''))	== 0: MediaInfo['Title']	= file[file.rfind("/")+1:].decode("utf-8")
		if len(MediaInfo.get('Artist', '')) == 0: MediaInfo['Artist']	= u'Unknown Artist'
		if len(MediaInfo.get('Album', ''))	== 0: MediaInfo['Ablum']	= u'Unknown Album'
		if len(MediaInfo.get('Genre', ''))	== 0: MediaInfo['Genre']	= u'Unknown'
		try: int(MediaInfo['TrackN'])
		except:	MediaInfo['TrackN'] = 0
		try: int(MediaInfo['DiscN'])
		except: MediaInfo['DiscN'] = 0
		return MediaInfo
	except: raise

def MP3info(file):
	MediaInfo = {'Title':'', 'Artist':'', 'Album':'', 'Genre':''}
	try:
		MediaInfo['Path'] = SubStringAfterKey(file, CWD)
		MP3File = eyed3.load(file)
		try:
			MediaInfo['Title'] = MP3File.tag.title
			if len(MediaInfo.get('Title', ''))	== 0: raise Exception
		except: MediaInfo['Title']	= file[file.rfind("/")+1:].decode("utf-8")
		try:
			MediaInfo['Artist'] = MP3File.tag.artist
			if len(MediaInfo.get('Artist', '')) == 0: raise Exception
		except: MediaInfo['Artist']	= u'Unknown Artist'
		try:
			MediaInfo['Album'] = MP3File.tag.album
			if len(MediaInfo.get('Album', ''))	== 0: raise Exception
		except: MediaInfo['Ablum']	= u'Unknown Album'
		try:
			MediaInfo['Genre'] = MP3File.tag.genre.name
			if len(MediaInfo.get('Genre', ''))	== 0: raise Exception
		except: MediaInfo['Genre']	= u'Unknown'
		try:
			MediaInfo['TrackN'] = MP3File.tag.track_num[0]
			int(MediaInfo['TrackN'])
		except: MediaInfo['TrackN'] = 0
		try:
			MediaInfo['DiscN'] = MP3File.tag.disc_num[0]
			int(MediaInfo['DiscN'])
		except: MediaInfo['DiscN'] = 0
		return MediaInfo
	except: raise

def M3Uinfo(file):
	PlayListName = "." + SubStringAfterKey(SubStringAfterKey(file, CWD)[:-4], '_Fiio X3 Playlists/')
	ThisPlayList = []
	m3u = open(file)
	for all in m3u:
		for line in all.splitlines():
			if line[:4] == '#EXT': continue
			elif CWD in line: ThisPlayList.append([PlayListName, PathTransform(SubStringAfterKey(line, CWD))])
			else: continue
	return ThisPlayList
		

def main():
	global NullDev, CWD
	NullDev = open('/dev/null', 'wb')
	CWD = os.getcwd() + "/"
	conn = sqlite3.connect(os.path.expanduser("~/Desktop/usrlocal_media.db"))
	c = conn.cursor()
	c.execute("DROP TABLE IF EXISTS VERSION_TABLE")
	c.execute("DROP TABLE IF EXISTS MEDIA_TABLE")
	c.execute("DROP TABLE IF EXISTS ALBUM_TABLE")
	c.execute("DROP TABLE IF EXISTS ARTIST_TABLE")
	c.execute("DROP TABLE IF EXISTS GENRE_TABLE")
	c.execute("DROP TABLE IF EXISTS TEMP_TABLE")
	c.execute("DROP TABLE IF EXISTS PLAYLIST_TABLE")
	c.execute("CREATE TABLE VERSION_TABLE (version_id INT);")
	c.execute("CREATE TABLE MEDIA_TABLE (id INT, path TEXT, name TEXT, ablum TEXT, artist TEXT, genre TEXT, album_id INT, artist_id INT, genre_id INT, index_00 INT, index_01 INT, source INT, collect INT, ck_id INT, has_child_file INT, begin_time INT, end_time INT, PRIMARY KEY(id))")
	c.execute("CREATE TABLE ALBUM_TABLE (album_id INTEGER PRIMARY KEY AUTOINCREMENT, album TEXT)")
	c.execute("CREATE TABLE ARTIST_TABLE (artist_id INTEGER PRIMARY KEY AUTOINCREMENT, artist TEXT)")
	c.execute("CREATE TABLE GENRE_TABLE (genre_id INTEGER PRIMARY KEY AUTOINCREMENT, genre TEXT)")
	c.execute("CREATE TABLE TEMP_TABLE (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT, name TEXT, album TEXT, artist TEXT, genre TEXT, TrackN INT, DiscN INT, end_time INT)")
	c.execute("CREATE TABLE PLAYLIST_TABLE (playlist TEXT, path TEXT)")

	AllInfoList = [] # The list that holds all dicts for all songs
	AllPlayList = [] # The list that holds Playlist info

	MP3FileList = []
	M4AFileList = []
	FLAFileList = [] # FLAC
	M3UFileList = [] # Playlist support
	IDKFileList = [] # I don't know!

	print "Scanning for files..."
	for fileList in os.walk(os.getcwd()):
		for fileName in fileList[2]:
			if   fileName.lower()[-4:] == '.mp3' : MP3FileList.append(''.join([fileList[0], '/', fileName]))
			elif fileName.lower()[-4:] == '.m4a' : M4AFileList.append(''.join([fileList[0], '/', fileName]))
			elif fileName.lower()[-4:] == 'flac' : FLAFileList.append(''.join([fileList[0], '/', fileName]))
			elif fileName.lower()[-4:] == '.m3u' : M3UFileList.append(''.join([fileList[0], '/', fileName]))
			else: IDKFileList.append(''.join([fileList[0], '/', fileName]))

	TotalFiles = len(M4AFileList) + len(MP3FileList)
	ProcessedFiles = 0
	for file in M4AFileList:
		ProcessedFiles += 1
		if (ProcessedFiles % 100 == 0): print "Processing files", ProcessedFiles, 'of', TotalFiles
		AllInfoList.append(M4Ainfo(file))
	for file in MP3FileList:
		ProcessedFiles += 1
		if (ProcessedFiles % 100 == 0): print "Processing files", ProcessedFiles, 'of', TotalFiles
		AllInfoList.append(MP3info(file))
	print "Processing database & playlists"
	for file in M3UFileList:
		AllPlayList.extend(M3Uinfo(file))
	
	c.execute("INSERT INTO VERSION_TABLE VALUES (2)")
	for item in AllInfoList:
		c.execute("INSERT INTO TEMP_TABLE VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)", (
		unicodedata.normalize('NFC', item.get('Path', "").decode("utf-8")),
		unicodedata.normalize('NFC', item.get('Title', u"Unknown Title")),
		unicodedata.normalize('NFC', item.get('Album', u"Unknown Album")),
		unicodedata.normalize('NFC', item.get('Artist', u"Unknown Artist")),
		unicodedata.normalize('NFC', item.get('Genre', u"Unknow Genre")),
		item.get('TrackN', "0"), item.get('DiscN', "0"), 0))

	for item in AllPlayList:
		c.execute("INSERT INTO PLAYLIST_TABLE VALUES (?, ?)", (unicodedata.normalize('NFC', item[0].decode("utf-8")), unicodedata.normalize('NFC', item[1].decode("utf-8"))))

	for row in c.execute("SELECT DISTINCT album FROM TEMP_TABLE").fetchall():
		c.execute("INSERT INTO ALBUM_TABLE VALUES (NULL, ?)", row)
	for row in c.execute("SELECT DISTINCT playlist FROM PLAYLIST_TABLE").fetchall():
		c.execute("INSERT INTO ALBUM_TABLE VALUES (NULL, ?)", row)
	for row in c.execute("SELECT DISTINCT artist FROM TEMP_TABLE").fetchall():
		c.execute("INSERT INTO ARTIST_TABLE VALUES (NULL, ?)", row)
	for row in c.execute("SELECT DISTINCT genre FROM TEMP_TABLE").fetchall():
		c.execute("INSERT INTO GENRE_TABLE VALUES (NULL, ?)", row)

	for row in c.execute("SELECT * FROM TEMP_TABLE").fetchall():
		id = row[0]
		path = PathTransform(row[1])
		name = row[2]
		album = row[3]
		album_id = c.execute("SELECT album_id FROM ALBUM_TABLE WHERE album = ?", (row[3],)).fetchone()[0]
		artist = row[4]
		artist_id = c.execute("SELECT artist_id FROM ARTIST_TABLE WHERE artist = ?", (row[4],)).fetchone()[0]
		genre = row[5]
		genre_id = c.execute("SELECT genre_id FROM GENRE_TABLE WHERE genre = ?", (row[5],)).fetchone()[0]
		ck_id = row[7]*100 + row[6]
		c.execute("INSERT INTO MEDIA_TABLE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, 0, ?, 0, 0, 0)", (id, path, name, album, artist, genre, album_id, artist_id, genre_id, ck_id))
	
	PlaylistN = c.execute("SELECT id FROM MEDIA_TABLE ORDER BY id DESC LIMIT 1").fetchone()[0]
	for row in c.execute("SELECT * FROM PLAYLIST_TABLE").fetchall():
		album_id = c.execute("SELECT album_id FROM ALBUM_TABLE WHERE album = ? LIMIT 1", (row[0],)).fetchone()[0]
		for item in c.execute("SELECT * FROM MEDIA_TABLE WHERE path LIKE ? LIMIT 1", (row[1],)).fetchall():
			PlaylistN += 1
			c.execute("INSERT INTO MEDIA_TABLE VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, 0, ?, 0, 0, 0)", (PlaylistN, item[1], item[2], row[0], item[4], item[5], album_id, item[7], item[8], PlaylistN))
		
	
	print "Total tracks:", len(M4AFileList)+len(MP3FileList)
	c.execute("DROP TABLE IF EXISTS TEMP_TABLE")
	c.execute("DROP TABLE IF EXISTS PLAYLIST_TABLE")
	c.execute("VACUUM")

	conn.commit()
	conn.close()

if __name__ == "__main__": main()
