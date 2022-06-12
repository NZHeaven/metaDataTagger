import base64
import os
from mutagen.mp3 import MP3
import subprocess
import requests
from mutagen.easyid3 import EasyID3
import argparse

album = ""

def handleArgs():
    parser = argparse.ArgumentParser(description='Scan Designated Folder for Music files and Tag Metadata if missing')
    parser.add_argument('folderpath',type=str,help='Path to Root Folder Containing the Music')
    parser.add_argument('album', type=str,help='Default Album Name')
    return parser.parse_args() 

def searchFiles(folderpath:str):
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            if file.endswith((".mp3",".wav")):
                if checkMetaDataExists(os.path.join(root,file)):
                    print(f"\u001b[31m Metadata exists skipping: {file} \u001b[0m")
                else:
                    print(f"\u001b[32m Metadata does not exist, Fetching Metadata for: {file} \u001b[0m")
                    getBase64String(os.path.join(root,file))
            
def getBase64String(musicFilePath:str):
    #Convert file to raw type, get length, extract 7s of audio save to a pcm(Binary) file
    # Get Length
    audio = MP3(musicFilePath)
    length = audio.info.length
    
    #Convert to a temp raw file
    #ffmpeg -i yt_synced_Big\ Iron.mp3 -acodec pcm_s16le -f s16le -ac 1 -ar 44100 -ss 30 -t 7 output.pcm
    command = f'ffmpeg -i "{musicFilePath}" -acodec pcm_s16le -f s16le -ac 1 -ar 44100 -ss {length/2} -t 7 -y temp.pcm'
    subprocess.Popen(command,shell=True, cwd= os.path.abspath(os.path.dirname(__file__))).wait()

    #Read raw binary audio data, convert to base64 string
    with open('temp.pcm', 'rb') as f:
         arr = f.read()
         data = base64.b64encode(arr)
    os.remove("temp.pcm")
    getMetaData(musicFilePath,data)
    
def getMetaData(musicFilePath:str, payload:str):
    url = "https://shazam.p.rapidapi.com/songs/detect"

    headers = {
	    "content-type": "text/plain",
	    "X-RapidAPI-Key": "0e4a61043bmsh40ecf3e44a197f5p1cca12jsnad7fedb81647",
	    "X-RapidAPI-Host": "shazam.p.rapidapi.com"
    }

    response = requests.request("POST", url, data=payload, headers=headers).json()

    artist = response['track']['subtitle']
    #print (response)
    print("\x1b[6;30;42m" + response['track']['subtitle'] + '\x1b[0m')
    tagMetaData(musicFilePath,artist,album)

def tagMetaData(musicFilePath:str,artist:str,album:str):
    audio = EasyID3(musicFilePath)
    audio['artist'] = artist
    audio['album'] = album
    audio.save() 

def checkMetaDataExists(musicFilePath:str):
    try:
        audio = EasyID3(musicFilePath)
        artist = audio['artist']
        return True
    except:
        return False

if __name__ == "__main__":
    args = handleArgs()
    album = args.album
    searchFiles(args.folderpath)