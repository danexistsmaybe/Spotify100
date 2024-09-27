import requests
from base64 import *
import json
from random import randint
from math import ceil

CLIENT_ID = "af39fd430e9445fdb3c05f0352504bf7"
SECRET = open("secret.txt",'r').read()

def getauthorizeurl():
	url = "https://accounts.spotify.com/authorize?"
	params = {
		"client_id": CLIENT_ID,
		"response_type": "code",
		"redirect_uri": "https://danexistsmaybe.xyz/",
		"scope": "playlist-modify-private playlist-modify-public playlist-read-private"
	}

	req = requests.Request("GET",url,params=params).prepare()
	return req.url

def addtoken(token,refreshtoken):
	file = open("tokens.txt",'a')
	file.write(token+'*'+refreshtoken+'\n')
	file.close()


def getaccesstoken(code):
	url = "https://accounts.spotify.com/api/token"
	params = {
		"grant_type": "authorization_code",
		"code": code,
		"redirect_uri": "https://danexistsmaybe.xyz/"
	}
	headers = {
		'Authorization': 'Basic '+b64encode((CLIENT_ID+':'+SECRET).encode('utf-8')).decode('utf-8'),
		'Content-Type': 'application/x-www-form-urlencoded'
	}	
	resp = requests.post(url=url,params=params,headers=headers)
	if resp.status_code==200:
		j = resp.json()
		addtoken(j["access_token"],j["refresh_token"])
		print("Time to be alive: ",j["expires_in"])
	else:
		print(resp.status_code)
		print(resp.text)


def refreshaccesstokens():
	tokens = open("tokens.txt",'r').read().split('\n')[:-1]
	newtokens = []
	for tokenline in tokens:
		rtoken = tokenline.split('*')[1]
		url = "https://accounts.spotify.com/api/token"
		params = {
			"grant_type": "refresh_token",
			"refresh_token": rtoken,
			"client_id": CLIENT_ID
		}
		headers = {
			'Content-Type': 'application/x-www-form-urlencoded',
			'Authorization': 'Basic '+b64encode((CLIENT_ID+':'+SECRET).encode('utf-8')).decode('utf-8')
		}	
		resp = requests.post(url=url,params=params,headers=headers)
		if resp.status_code==200:
			j = resp.json()
			if j.get("refresh_token")!=None: newtokens.append(j["access_token"]+'*'+j["refresh_token"])
			else: newtokens.append(j["access_token"]+'*'+rtoken)
			print("Time to be alive: ",j["expires_in"])
		else:
			print(resp.status_code)
			print(resp.text)
			newtokens.append(tokenline)
	if len(newtokens)>0:
		file = open("tokens.txt",'w')
		file.write("\n".join(newtokens)+"\n")
		file.close()
	else: print("Something went wrong in refreshing tokens")

def getfirsttoken():
	tokens = open("tokens.txt",'r').read()
	if len(tokens)>0:
		return tokens.split('\n')[0]
	return False

def get(token,endpoint="",head={},params={}):
	url = "https://api.spotify.com/"+endpoint
	head["Authorization"] = "Bearer "+token
	resp = requests.get(url=url,params=params,headers=head)
	if resp.status_code==200:
		return resp.json()
	else:
		print(resp.status_code, resp.text)
		quit()

def post(token,endpoint="",head={},params={},data={}):
	url = "https://api.spotify.com/"+endpoint
	head["Authorization"] = "Bearer "+token
	resp = requests.post(url=url,params=params,headers=head,data=json.dumps(data))
	if resp.status_code==200:
		return resp.json
	else:
		print(resp.status_code, resp.text)
		quit()

def delete(token,endpoint="",head={},params={},data={}):
	url = "https://api.spotify.com/"+endpoint
	head["Authorization"] = "Bearer "+token
	resp = requests.delete(url=url,params=params,headers=head,data=data)
	if resp.status_code==200:
		return resp.json
	else:
		print(resp.status_code, resp.text)
		quit()

def getuserid(token):
	resp = get(token,"v1/me",head={"Authorization": "Bearer "+token})
	return resp["id"]

def getplaylists(token,userid):
	playlists = []
	offset = 0
	while True:
		resp=get(token,endpoint="v1/users/"+userid+"/playlists",params={
			"user_id": userid,
			"limit": "50",
			"offset": str(offset)
		})
		if len(resp["items"])==0: break
		for playlist in resp["items"]:
			playlists.append(playlist)
		offset+=50
	return playlists

def getplaylist(token,userid,name):
	playlists = getplaylists(token,userid)
	for p in playlists:
		if p["name"]==name: return p["id"]
	return ""

def gettrackuris(token,playlistid):
	tracks = []
	offset = 0
	while True:
		resp=get(token,endpoint="v1/playlists/"+playlistid+"/tracks",params={
			"limit": "50",
			"offset": str(offset)
		})
		if len(resp["items"])==0: break
		for item in resp["items"]:
			tracks.append(item["track"]["uri"])
		offset+=50
	return tracks

def deleteallfromplaylist(token,playlistid):
	trackuris = gettrackuris(token,playlistid)
	tracks = []
	for uri in trackuris: tracks.append({"uri": uri})

	endpoint = "v1/playlists/"+playlistid+"/tracks"
	headers = {"Content-Type": "application/json"}
	data =  {"tracks": tracks}
	delete(token,endpoint=endpoint,head=headers,data=json.dumps(data))

def sampleplaylists(token,userid,exclude=[]):
	playlists = getplaylists(token,userid)
	sample=[]

	print("Looping through playlists...")
	i=0
	for playlist in playlists: 
		if playlist["name"] in exclude: continue
		tracks = gettrackuris(token,playlist["id"])
		r = randint(0,len(tracks)-1)
		sample.append(tracks[r])

		# Progress bar:
		prog = ceil(10*(i/len(playlists)))
		print("\r[" + "="*prog + "-"*(10-prog) + "]",end="")
		i+=1
	print()
	return sample

def addtrackstoplaylist(token,playlistid,tracks):
	print("Adding list of "+str(len(tracks))+" to playlist...")
	endpoint = "v1/playlists/" + playlistid + "/tracks"
	headers = {"Content-Type": "application/json"}
	data = {"uris": tracks, "position": 0}
	post(token,endpoint,head=headers,data=data)
	print("Finished adding tracks.")

  



def main():
	#refreshaccesstokens()
	token = getfirsttoken()
	userid=getuserid(token)
	sample = sampleplaylists(token,userid,exclude=["My Playlist #100"])
	playlist = getplaylist(token,userid,"My Playlist #100")
	if playlist != "": addtrackstoplaylist(token,playlist,sample)
	else: print("Could not get playlist")
	

if __name__=="__main__":
	main()
	quit()


url = 'https://api.spotify.com'


headers = {
    'Authorization': 'Bearer '+token
}

resp = requests.get(url, headers=headers)

print(resp.status_code)
#BQBirGqgmNbYbyWF2C5ashb6a8KWkYOZHX4xRfxHB7Cn_bB4QqekX-FyS646YIGFBJ2Ekwp0GsJJUL4X1VWiHVFvsiaArsvVRsL9ZLkNftpSF-W5XkjTFDkY9QUHTX13kdOp4Pfm2qV5RRFY8niTEDwRGKfzhQzrrZkkKHlAQwTwYoskbrOnFix83osUWtKbEzhy2u8j4CHy2Q*AQDBry5PRe7facvyXo43paRzWHHQ4YISk91f8WElCgSgxTtDSTtQRy7q76cHWPWfBd-9RmkvRcClL9pVPgba-P_R02sVBeLGCal2Drki0FMGiNhHjBs_mRFO0LlEfipUkRk
