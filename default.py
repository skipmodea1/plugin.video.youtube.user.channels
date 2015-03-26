#!/usr/bin/python
# -*- coding: utf-8 -*-

############################################################################################################################################
#                                                                                                                                          #
# youtube.user.channels - Addon for Kodi                                                                                                   #                                                                                                         #
#                                                                                                                                          #
# for example for the youtube User 'Vice': "https://www.youtube.com/user/vice/channels"                                                    #  
#                                                                                                                                          #
############################################################################################################################################
#                                                                                                                                          #
# Coding by Skipmode A1                                                                                                                    #
#                                                                                                                                          # 
# Credits:                                                                                                                                 #
#   * AddonScriptorDE                                                 Author of a lot of great addons                                      #
#   * Youtube                                                         [https://www.youtube.com]                                            #
#   * Team Kodi @ kodi.org                                            [http://kodi.org/]                                                   #
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup      [http://www.crummy.com/software/BeautifulSoup/]                      #
#                                                                                                                                          #
############################################################################################################################################

import urllib
import urllib2
import socket
import sys
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
viewMode = str(addon.getSetting("viewIDVideos"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
addonUserdataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
youtubeUrl = "https://www.youtube.com"

if not os.path.isdir(addonUserdataFolder):
    os.mkdir(addonUserdataFolder)

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()


def listUserChannels(youtubeUser):
    if youtubeUser == "":
        pass
    else:
        userUrl = youtubeUrl + "/user/" + youtubeUser + "/channels"
        listChannels(userUrl)


def listChannels(url):
    content = getUrl(url)
    soup = BeautifulSoup( content )

#div class="yt-lockup-content">
#<a class="yt-uix-sessionlink yt-uix-tile-link  spf-link  yt-ui-ellipsis yt-ui-ellipsis-2" dir="ltr" title="VICE News"  aria-describedby="description-id-647047" data-sessionlink="ved=CAgQvxs&amp;ei=huyYVObiFovHcePWgYAJ" href="/user/vicenews">VICE News
    items = soup.findAll('div', attrs={'class': re.compile("^yt-lockup-content")})

#   Put the name and url in an Array
    itemsIndex = 0
    itemArray = []
    for item in items:
        name = item.a["title"]
        name = cleanName(name)
        itemArray.append(name + youtubeUrl + str(item.a["href"]))
        itemsIndex = itemsIndex + 1
        
    itemsIndexMax = itemsIndex - 1
    
#   Sort the Array
    itemArray.sort()
    
    previousItem = ""
    itemsIndex = 0
    for item in itemArray:
        if str(item).upper() == previousItem:
#           Skip items with the same name
            continue
        else:
            previousItem = str(item).upper()
        
        pos_http = str(item).find(youtubeUrl)
        name = item[0:pos_http]
        url = item[pos_http:]
        thumb = ""
        date = ""
        desc = ""
        addShowDir(name, url, 'listShows', thumb, desc)     


def endUserChannels(): 
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE )
    ok = xbmcplugin.endOfDirectory(pluginhandle)        
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    return ok


def listShows(url):
    content = getUrl(url)
    soup = BeautifulSoup( content )
    
#<a href="/playlist?list=PLw613M86o5o7q1cjb26MfCgdxJtshvRZ-" class="yt-uix-sessionlink branded-page-module-title-link spf-nolink" data-sessionlink="ei=6KeXVImTDIvmcMKNgNAG">
    items = soup.findAll('a', attrs={'href': re.compile("^/playlist")})
    for item in items:
        if str(item).find("branded-page-module-title-text") > 0:
            pass
        else:
#       skip items that don't contain this: branded-page-module-title-text
            continue
                  
        name = item.text
        name = cleanName(name)
        url = youtubeUrl + str(item["href"])
        thumb = ""
        date = ""
        desc = ""
        addShowDir(name, url, 'listVideos', thumb, desc)

    xbmcplugin.endOfDirectory(pluginhandle)        
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')         


def listVideos(url):
    content = getUrl(url)
    soup = BeautifulSoup( content )

#    <tr class="pl-video yt-uix-tile " data-video-id="KWFPdmAhyes" data-set-video-id="" data-title="Violent Protests in Athens: Greece&#39;s Young Anarchists (Part 2)">
    items = soup.findAll('tr', attrs={'class': re.compile("^pl-video")})
    for item in items:
        name = item["data-title"]
        name = cleanName(name)
        youtubeID = item["data-video-id"]
        if xbox:
            url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
        else:
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
        thumb = "https:" + str(item.img["src"])
        date = ""
        desc = ""
        addLink(name, url, 'playVideo', thumb, date+"\n"+desc)

    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
           
           
def addShowDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    playListInfos = "###MODE###=ADD###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=favs&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def playVideo(url):
    streamUrl = url
    listitem = xbmcgui.ListItem(path=streamUrl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanName(name):
    name = name.strip()
    name = name.capitalize()
    name = name.encode('utf-8')
    name = name.replace("&lt;", "<")
    name = name.replace("&gt;", ">")
    name = name.replace("&amp;", "&")
    name = name.replace("&#39;", "'")
    name = name.replace("&#039;", "'")
    name = name.replace("&quot;", "'")
    name = name.replace("&szlig;", "ß")
    name = name.replace("&ndash;", "-")
    name = name.replace("&Auml;", "Ä")
    name = name.replace("&Uuml;", "Ü")
    name = name.replace("&Ouml;", "Ö")
    name = name.replace("&auml;", "ä")
    name = name.replace("&uuml;", "ü")
    name = name.replace("&ouml;", "ö")
    name = name.replace(' i ',' I ')
    name = name.replace(' ii ',' II ')
    name = name.replace(' iii ',' III ')
    name = name.replace(' iv ',' IV ')
    name = name.replace(' v ',' V ')
    name = name.replace(' vi ',' VI ')
    name = name.replace(' vii ',' VII ')
    name = name.replace(' viii ',' VIII ')
    name = name.replace(' ix ',' IX ')
    name = name.replace(' x ',' X ')
    name = name.replace(' xi ',' XI ')
    name = name.replace(' xii ',' XII ')
    name = name.replace(' xiii ',' XIII ')
    name = name.replace(' xiv ',' XIV ')
    name = name.replace(' xv ',' XV ')
    name = name.replace(' xvi ',' XVI ')
    name = name.replace(' xvii ',' XVII ')
    name = name.replace(' xviii ',' XVIII ')
    name = name.replace(' xix ',' XIX ')
    name = name.replace(' xx ',' XXX ')
    name = name.replace(' xxi ',' XXI ')
    name = name.replace(' xxii ',' XXII ')
    name = name.replace(' xxiii ',' XXIII ')
    name = name.replace(' xxiv ',' XXIV ')
    name = name.replace(' xxv ',' XXV ')
    name = name.replace(' xxvi ',' XXVI ')
    name = name.replace(' xxvii ',' XXVII ')
    name = name.replace(' xxviii ',' XXVIII ')
    name = name.replace(' xxix ',' XXIX ')
    name = name.replace(' xxx ',' XXX ')
    return name


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+str(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listShows':
    listShows(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    listUserChannels(addon.getSetting("youtubeUser01"))
    listUserChannels(addon.getSetting("youtubeUser02"))
    listUserChannels(addon.getSetting("youtubeUser03"))
    listUserChannels(addon.getSetting("youtubeUser04"))
    listUserChannels(addon.getSetting("youtubeUser05"))
    listUserChannels(addon.getSetting("youtubeUser06"))
    listUserChannels(addon.getSetting("youtubeUser07"))
    listUserChannels(addon.getSetting("youtubeUser08"))
    listUserChannels(addon.getSetting("youtubeUser09"))
    listUserChannels(addon.getSetting("youtubeUser10"))
    endUserChannels()    