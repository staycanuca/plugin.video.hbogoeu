# encoding: utf-8
# base handler class for hbogo Kodi add-on
# Copyright (C) 2019 ArvVoid (https://github.com/arvvoid)
# Derived from version v.2.0-beta5 of the add-on, witch was initialy
# derived from https://github.com/billsuxx/plugin.video.hbogohu witch is
# derived from https://kodibg.org/forum/thread-504.html
# Relesed under GPL version 2
#########################################################
# http://hbogo.eu HBOGO HANDLER CLASS
#########################################################


from hbogolib.handler import HbogoHandler

import sys
import time
import urllib
import json
import base64
import hashlib

import xbmc
import xbmcgui
import xbmcplugin
import inputstreamhelper

class HbogoHandler_eu(HbogoHandler):

    def __init__(self, addon_id, handle, base_url, country, operator_name):
        HbogoHandler.__init__(self, addon_id, handle, base_url)
        self.operator_name=operator_name
        self.log("OPERATOR: " + self.operator_name)
        self.op_id=country[0]
        self.log("OPERATOR ID: " + self.op_id)
        self.COUNTRY_CODE_SHORT = country[2]
        self.log("OPERATOR COUNTRY_CODE_SHORT: " + self.COUNTRY_CODE_SHORT)
        self.COUNTRY_CODE = country[3]
        self.log("OPERATOR COUNTRY_CODE: " + self.COUNTRY_CODE)
        self.DEFAULT_LANGUAGE = country[4]
        self.log("DEFAULT HBO GO LANGUAGE: " + self.DEFAULT_LANGUAGE)
        self.DOMAIN_CODE = country[1]
        self.is_web=country[5]
        self.log("WEB OPERATOR: " + str(self.is_web))
        self.REDIRECT_URL=country[6]
        self.log("OPERATOR REDIRECT: " + str(self.REDIRECT_URL))
        self.SPECIALHOST_URL=country[8]
        self.log("OPERATOR SPECIAL HOST URL: " + str(self.SPECIALHOST_URL))
        #GEN API URLS

        # API URLS
        self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        if self.language(32000) == 'ENG':  # only englih or the default language for the selected operator is allowed
            self.LANGUAGE_CODE = 'ENG'

        # check if default language is forced
        if self.addon.getSetting('deflang') == 'true':
            self.LANGUAGE_CODE = self.DEFAULT_LANGUAGE

        self.LICENSE_SERVER = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/'

        self.API_HOST = self.COUNTRY_CODE_SHORT + 'api.hbogo.eu'

        if len(self.SPECIALHOST_URL)>0:
            self.API_HOST_REFERER = self.SPECIALHOST_URL
            self.API_HOST_ORIGIN = self.SPECIALHOST_URL
        else:
            self.API_HOST_REFERER = 'https://hbogo.' + self.DOMAIN_CODE + '/'
            self.API_HOST_ORIGIN = 'https://www.hbogo.' + self.DOMAIN_CODE

        self.API_HOST_GATEWAY = 'https://gateway.hbogo.eu'
        self.API_HOST_GATEWAY_REFERER = 'https://gateway.hbogo.eu/signin/form'

        self.API_URL_SILENTREGISTER = 'https://' + self.COUNTRY_CODE_SHORT + '.hbogo.eu/services/settings/silentregister.aspx'

        self.API_URL_SETTINGS = 'https://' + self.API_HOST + '/v7/Settings/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_AUTH_WEBBASIC = 'https://api.ugw.hbogo.eu/v3.0/Authentication/' + self.COUNTRY_CODE + '/JSON/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_AUTH_OPERATOR = 'https://' + self.COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu/v2.1/Authentication/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_CUSTOMER_GROUP = 'https://' + self.API_HOST + '/v7/CustomerGroup/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_GROUPS = 'https://' + self.API_HOST + '/v5/Groups/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_CONTENT = 'http://' + self.API_HOST + '/v5/Content/json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'
        self.API_URL_PURCHASE = 'https://' + self.API_HOST + '/v5/Purchase/Json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_SEARCH = 'https://' + self.API_HOST + '/v5/Search/Json/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM + '/'

        self.API_URL_GET_WEB_OPERATORS = 'https://api.ugw.hbogo.eu/v3.0/Operators/' + self.COUNTRY_CODE + '/JSON/' + self.LANGUAGE_CODE + '/' + self.API_PLATFORM
        self.API_URL_GET_OPERATORS = 'https://' + self.COUNTRY_CODE_SHORT + 'gwapi.hbogo.eu/v2.1/Operators/json/' + self.COUNTRY_CODE + '/' + self.API_PLATFORM

        self.individualization = ""
        self.goToken = ""
        self.customerId = ""
        self.GOcustomerId = ""
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        self.FavoritesGroupId = ""

        self.loggedin_headers = {
            'User-Agent': self.UA,
            'Accept': '*/*',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Referer': self.API_HOST_REFERER,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.API_HOST_ORIGIN,
            'X-Requested-With': 'XMLHttpRequest',
            'GO-Language': self.LANGUAGE_CODE,
            'GO-requiredPlatform': self.GO_REQUIRED_PLATFORM,
            'GO-Token': '',
            'GO-SessionId': '',
            'GO-swVersion': self.GO_SW_VERSION,
            'GO-CustomerId': '',
            'Connection': 'keep-alive',
            'Accept-Encoding': ''
        }

    def storeIndiv(self, indiv, custid):
        self.individualization = self.addon.getSetting('individualization')
        if self.individualization == "":
            self.addon.setSetting('individualization', indiv)
            self.addon.individualization = indiv

        self.customerId = self.addon.getSetting('customerId')
        if self.customerId == "":
            self.addon.setSetting('customerId', custid)
            self.customerId = custid

    def storeFavgroup(self, favgroupid):
        self.FavoritesGroupId = self.addon.getSetting('FavoritesGroupId')
        if self.FavoritesGroupId == "":
            self.addon.setSetting('FavoritesGroupId', favgroupid)
            self.FavoritesGroupId = favgroupid

    def silentRegister(self):
        self.log("DEVICE REGISTRATION")
        jsonrsp = self.get_from_hbogo(self.API_URL_SILENTREGISTER)
        self.log("DEVICE REGISTRATION: " + str(jsonrsp))
        try:
            if jsonrsp['Data']['ErrorMessage']:
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['Data']['ErrorMessage'])
                self.logout()
                return
            indiv = jsonrsp['Data']['Customer']['CurrentDevice']['Individualization']
            custid = jsonrsp['Data']['Customer']['CurrentDevice']['Id']
            self.storeIndiv(indiv, custid)

            self.sessionId = jsonrsp['Data']['SessionId']
        except:
            self.logout()
            self.log("DEVICE REGISTRATION: UNEXPECTED PROBLEM")
            return
        self.log("DEVICE REGISTRATION: OK")
        return jsonrsp

    def getFavoriteGroup(self):
        jsonrsp = self.get_from_hbogo(self.API_URL_SETTINGS)

        self.favgroupId = jsonrsp['FavoritesGroupId']
        self.storeFavgroup(self.favgroupId)

    def chk_login(self):
        return (self.loggedin_headers['GO-SessionId']!='00000000-0000-0000-0000-000000000000' and len(self.loggedin_headers['GO-Token'])!=0 and len(self.loggedin_headers['GO-CustomerId'])!=0)

    def logout(self):
        self.log("Loging out")
        self.del_login()
        self.goToken = ""
        self.customerId = ""
        self.GOcustomerId = ""
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        self.loggedin_headers['GO-SessionId'] = str(self.sessionId)
        self.loggedin_headers['GO-Token'] = str(self.goToken)
        self.loggedin_headers['GO-CustomerId'] = str(self.GOcustomerId)


    def login(self):
        self.log("Using operator: " + str(self.op_id))

        username = self.addon.getSetting('username')
        password = self.addon.getSetting('password')
        self.customerId = self.addon.getSetting('customerId')
        self.individualization = self.addon.getSetting('individualization')
        self.FavoritesGroupId = self.addon.getSetting('FavoritesGroupId')

        if (self.individualization == "" or self.customerId == ""):
            self.silentRegister()

        if (self.FavoritesGroupId == ""):
            self.getFavoriteGroup()

        if (username == "" or password == ""):
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, self.LB_NOLOGIN)
            self.addon.openSettings()
            sys.exit()
            return

        login_hash = hashlib.sha224(self.individualization + self.customerId + self.FavoritesGroupId + username + password + self.op_id).hexdigest()
        self.log("LOGIN HASH: " + login_hash)

        loaded_session = self.load_obj(self.addon_id + "_session")

        if loaded_session != None:
            # sesion exist if valid restore
            self.log("SAVED SESSION LOADED")
            if loaded_session["hash"] == login_hash:
                self.log("HASH IS VALID")
                if time.time() < (loaded_session["time"] + (self.SESSION_VALIDITY * 60 * 60)):
                    self.log("NOT EXPIRED RESTORING...")
                    # valid loaded sesion restor and exit login
                    if self.sensitive_debug:
                        self.log("Restoring login from saved: " + str(loaded_session))
                    else:
                        self.log("Restoring login from saved: [OMITTED FOR PRIVACY]")
                    self.loggedin_headers = loaded_session["headers"]
                    self.sessionId = self.loggedin_headers['GO-SessionId']
                    self.goToken = self.loggedin_headers['GO-Token']
                    self.GOcustomerId = self.loggedin_headers['GO-CustomerId']
                    if self.sensitive_debug:
                        self.log("Login restored - Token" + str(self.goToken))
                        self.log("Login restored - Customer Id" + str(self.GOcustomerId))
                        self.log("Login restored - Session Id" + str(self.sessionId))
                    else:
                        self.log("Login restored - Token  [OMITTED FOR PRIVACY]")
                        self.log("Login restored - Customer Id  [OMITTED FOR PRIVACY]")
                        self.log("Login restored - Session Id [OMITTED FOR PRIVACY]")
                    return

        headers = {
            'Origin': self.API_HOST_GATEWAY,
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'User-Agent': self.UA,
            'GO-Token': '',
            'Accept': 'application/json',
            'GO-SessionId': '',
            'Referer': self.API_HOST_GATEWAY_REFERER,
            'Connection': 'keep-alive',
            'GO-CustomerId': '00000000-0000-0000-0000-000000000000',
            'Content-Type': 'application/json',
        }

        if self.is_web:
            url = self.API_URL_AUTH_WEBBASIC
        else:
            url = self.API_URL_AUTH_OPERATOR

        if len(self.REDIRECT_URL) > 0:
            self.log("OPERATOR WITH LOGIN REDIRECT DETECTED, THE LOGIN WILL PROBABLY FAIL, NOT IMPLEMENTED, more details https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
            # EXPLANATION
            # ------------
            # For a few operators the login is not performed directly using the hbogo api. Instead the user is redirected to the operator website
            # the login is performed there, and then the operator login the user on hbogo and redirect back.
            # What exactly happens and how, will have to be figured out and then implemented in the add-on for those operators to work.
            # For more information go to https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5

        data_obj = {
            "Action": "L",
            "AppLanguage": None,
            "ActivationCode": None,
            "AllowedContents": [],
            "AudioLanguage": None,
            "AutoPlayNext": False,
            "BirthYear": 1,
            "CurrentDevice": {
                "AppLanguage": "",
                "AutoPlayNext": False,
                "Brand": "Chromium",
                "CreatedDate": "",
                "DeletedDate": "",
                "Id": "00000000-0000-0000-0000-000000000000",
                "Individualization": self.individualization,
                "IsDeleted": False,
                "LastUsed": "",
                "Modell": "71",
                "Name": "",
                "OSName": "Ubuntu",
                "OSVersion": "undefined",
                "Platform": self.API_PLATFORM,
                "SWVersion": "3.3.9.6418.2100",
                "SubtitleSize": ""
            },
            "CustomerCode": "",
            "DebugMode": False,
            "DefaultSubtitleLanguage": None,
            "EmailAddress": username,
            "FirstName": "",
            "Gender": 0,
            "Id": "00000000-0000-0000-0000-000000000000",
            "IsAnonymus": True,
            "IsPromo": False,
            "Language": self.LANGUAGE_CODE,
            "LastName": "",
            "Nick": "",
            "NotificationChanges": 0,
            "OperatorId": self.op_id,
            "OperatorName": "",
            "OperatorToken": "",
            "ParentalControl": {
                "Active": False,
                "Password": "",
                "Rating": 0,
                "ReferenceId": "00000000-0000-0000-0000-000000000000"
            },
            "Password": password,
            "PromoCode": "",
            "ReferenceId": "00000000-0000-0000-0000-000000000000",
            "SecondaryEmailAddress": "",
            "SecondarySpecificData": None,
            "ServiceCode": "",
            "SubscribeForNewsletter": False,
            "SubscState": None,
            "SubtitleSize": "",
            "TVPinCode": "",
            "ZipCode": ""
        }

        data = json.dumps(data_obj)
        if self.sensitive_debug:
            self.log("PERFORMING LOGIN: " + str(data))
        else:
            self.log("PERFORMING LOGIN")
        jsonrspl = self.send_login_hbogo(url, headers, data)

        try:
            if jsonrspl['ErrorMessage']:
                self.log("LOGIN ERROR: " + str(jsonrspl['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, str(jsonrspl['ErrorMessage']))
                if len(REDIRECT_URL) > 0:
                    xbmcgui.Dialog().ok(self.LB_ERROR, "OPERATOR WITH LOGIN REDIRECTION DETECTED. LOGIN REDIRECTION IS NOT CURRENTLY IMPLEMENTED. TO FIND OUT MORE ABOUTE THE ISSUE AND/OR CONTRIBUTE GO TO https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
                self.logout()
                return
        except:
            pass

        try:
            self.customerId = jsonrspl['Customer']['CurrentDevice']['Id']
            self.individualization = jsonrspl['Customer']['CurrentDevice']['Individualization']
        except:
            self.log("GENERIC LOGIN ERROR")
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "GENERIC LOGIN ERROR")
            if len(self.REDIRECT_URL) > 0:
                xbmcgui.Dialog().ok(self.LB_ERROR, "OPERATOR WITH LOGIN REDIRECTION DETECTED. LOGIN REDIRECTION IS NOT CURRENTLY IMPLEMENTED. TO FIND OUT MORE ABOUTE THE ISSUE AND/OR CONTRIBUTE GO TO https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
            self.logout()
            return
        self.sessionId = '00000000-0000-0000-0000-000000000000'
        try:
            self.sessionId = jsonrspl['SessionId']
        except:
            self.sessionId = '00000000-0000-0000-0000-000000000000'
        if self.sessionId == '00000000-0000-0000-0000-000000000000' or len(self.sessionId) != 36:
            self.log("GENERIC LOGIN ERROR")
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, "GENERIC LOGIN ERROR")
            if len(self.REDIRECT_URL) > 0:
                xbmcgui.Dialog().ok(self.LB_ERROR, "OPERATOR WITH LOGIN REDIRECTION DETECTED. LOGIN REDIRECTION IS NOT CURRENTLY IMPLEMENTED. TO FIND OUT MORE ABOUTE THE ISSUE AND/OR CONTRIBUTE GO TO https://github.com/arvvoid/plugin.video.hbogoeu  ISSUE #5 ")
            self.logout()
            return
        else:
            self.goToken = jsonrspl['Token']
            self.GOcustomerId = jsonrspl['Customer']['Id']
            if self.sensitive_debug:
                self.log("Login sucess - Token" + str(self.goToken))
                self.log("Login sucess - Customer Id" + str(self.GOcustomerId))
                self.log("Login sucess - Session Id" + str(self.sessionId))
            else:
                self.log("Login sucess - Token  [OMITTED FOR PRIVACY]")
                self.log("Login sucess - Customer Id  [OMITTED FOR PRIVACY]")
                self.log("Login sucess - Session Id [OMITTED FOR PRIVACY]")
            self.loggedin_headers['GO-SessionId'] = str(self.sessionId)
            self.loggedin_headers['GO-Token'] = str(self.goToken)
            self.loggedin_headers['GO-CustomerId'] = str(self.GOcustomerId)
            # save the session with validity of n hours to not relogin every run of the add-on
            saved_session = {

                "hash": login_hash,
                "headers": self.loggedin_headers,
                "time": time.time()

            }
            if self.sensitive_debug:
                self.log("SAVING SESSION: " + str(saved_session))
            else:
                self.log("SAVING SESSION: [OMITTED FOR PRIVACY]")
            self.save_obj(saved_session, self.addon_id + "_session")



    def categories(self):
        if not self.chk_login():
            self.login()
        self.setDispCat(self.operator_name)
        self.addCat(self.LB_SEARCH, self.LB_SEARCH, self.md + 'search.png', 4)

        if (self.FavoritesGroupId == ""):
            self.getFavoriteGroup()

        if (self.FavoritesGroupId != ""):
            self.addCat(self.LB_MYPLAYLIST, self.API_URL_CUSTOMER_GROUP + self.FavoritesGroupId + '/-/-/-/1000/-/-/false', self.md + 'FavoritesFolder.png', 1)

        jsonrsp = self.get_from_hbogo(self.API_URL_GROUPS)

        try:
            if jsonrsp['ErrorMessage']:
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
        except:
            pass

        for cat in jsonrsp['Items']:
            self.addCat(cat['Name'].encode('utf-8', 'ignore'), cat['ObjectUrl'].replace('/0/{sort}/{pageIndex}/{pageSize}/0/0', '/0/0/1/1024/0/0'), self.md + 'DefaultFolder.png', 1)

        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(self.handle)

    def list(self, url):
        if not self.chk_login():
            self.login()
        self.log("List: " + str(url))

        if not self.chk_login():
            self.login()

        jsonrsp = self.get_from_hbogo(url)

        try:
            if jsonrsp['ErrorMessage']:
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
        except:
            pass
        # If there is a subcategory / genres
        if len(jsonrsp['Container']) > 1:
            for Container in range(0, len(jsonrsp['Container'])):
                self.addCat(jsonrsp['Container'][Container]['Name'].encode('utf-8', 'ignore'),
                       jsonrsp['Container'][Container]['ObjectUrl'], self.md + 'DefaultFolder.png', 1)
        else:
            for title in jsonrsp['Container'][0]['Contents']['Items']:
                if title['ContentType'] == 1 or title['ContentType'] == 3:  # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                    self.addLink(title, 5)
                else:
                    self.addDir(title, 2, "tvshow")
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.setContent(self.handle, self.use_content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def season(self, url):
        if not self.chk_login():
            self.login()
        self.log("Season: " + str(url))
        jsonrsp = self.get_from_hbogo(url)

        try:
            if jsonrsp['ErrorMessage']:
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
        except:
            pass
        for season in jsonrsp['Parent']['ChildContents']['Items']:
            self.addDir(season, 3, "season")
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.setContent(self.handle, self.use_content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def episode(self, url):
        if not self.chk_login():
            self.login()
        self.log("Episode: " + str(url))
        jsonrsp = self.get_from_hbogo(url)

        try:
            if jsonrsp['ErrorMessage']:
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
        except:
            pass

        for episode in jsonrsp['ChildContents']['Items']:
            self.addLink(episode, 5)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.setContent(self.handle, self.use_content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def search(self):
        if not self.chk_login():
            self.login()
        keyb = xbmc.Keyboard(self.search_string, self.LB_SEARCH_DESC)
        keyb.doModal()
        if (keyb.isConfirmed()):
            searchText = urllib.quote_plus(keyb.getText())
            if searchText == "":
                self.addCat(self.LB_SEARCH_NORES, self.LB_SEARCH_NORES, self.md + 'DefaultFolderBack.png', '')
            else:
                self.addon.setSetting('lastsearch', searchText)
                self.log("Performing search: " + str(self.API_URL_SEARCH + searchText.decode('utf-8', 'ignore').encode('utf-8', 'ignore') + '/0'))
                jsonrsp = self.get_from_hbogo(self.API_URL_SEARCH + searchText.decode('utf-8', 'ignore').encode('utf-8', 'ignore') + '/0')
                self.log(str(jsonrsp))

                try:
                    if jsonrsp['ErrorMessage']:
                        self.log("Search Error: " + str(jsonrsp['ErrorMessage']))
                        xbmcgui.Dialog().ok(self.LB_ERROR, jsonrsp['ErrorMessage'])
                except:
                    pass

                br = 0
                for item in jsonrsp['Container'][0]['Contents']['Items']:
                    if item['ContentType'] == 1 or item['ContentType'] == 7 or item['ContentType'] == 3:  # 1,7=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
                        self.addLink(item, 5)
                    else:
                        self.addDir(item, 2, "season")
                    br = br + 1
                if br == 0:
                    self.addCat(self.LB_SEARCH_NORES, self.LB_SEARCH_NORES, self.md + 'DefaultFolderBack.png', '')

        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(
            handle=self.handle,
            sortMethod=xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.setContent(self.handle, self.use_content_type)
        xbmcplugin.endOfDirectory(self.handle)

    def play(self, url, content_id):
        self.log("Play: " + str(url))

        if not self.chk_login():
            self.login()
        if not self.chk_login():
            self.log("NO LOGED IN ABORTING PLAY")
            xbmcgui.Dialog().ok(self.LB_LOGIN_ERROR, self.language(32103))
            self.logout()
            return
        purchase_payload = '<Purchase xmlns="go:v5:interop"><AllowHighResolution>true</AllowHighResolution><ContentId>' + content_id + '</ContentId><CustomerId>' + self.GOcustomerId + '</CustomerId><Individualization>' + self.individualization + '</Individualization><OperatorId>' + self.op_id + '</OperatorId><ClientInfo></ClientInfo><IsFree>false</IsFree><UseInteractivity>false</UseInteractivity></Purchase>'
        self.log("Purchase payload: " + str(purchase_payload))
        purchase_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': '',
            'Accept-Language': self.ACCEPT_LANGUAGE,
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'GO-CustomerId': str(self.GOcustomerId),
            'GO-requiredPlatform': self.GO_REQUIRED_PLATFORM,
            'GO-SessionId': str(self.sessionId),
            'GO-swVersion': self.GO_SW_VERSION,
            'GO-Token': str(self.goToken),
            'Host': self.API_HOST,
            'Referer': self.API_HOST_REFERER,
            'Origin': self.API_HOST_ORIGIN,
            'User-Agent': self.UA
        }
        self.log("Requesting purchase: " + str(self.API_URL_PURCHASE))
        jsonrspp = self.send_purchase_hbogo(self.API_URL_PURCHASE, purchase_payload, purchase_headers)
        self.log("Purchase response: " + str(jsonrspp))

        try:
            if jsonrspp['ErrorMessage']:
                self.log("Purchase error: " + str(jsonrspp['ErrorMessage']))
                xbmcgui.Dialog().ok(self.LB_ERROR, jsonrspp['ErrorMessage'])
                self.logout()
                return
        except:
            pass

        MediaUrl = jsonrspp['Purchase']['MediaUrl'] + "/Manifest"
        self.log("Media Url: " + str(jsonrspp['Purchase']['MediaUrl'] + "/Manifest"))
        PlayerSessionId = jsonrspp['Purchase']['PlayerSessionId']
        self.log("PlayerSessionId: " + str(jsonrspp['Purchase']['PlayerSessionId']))
        x_dt_auth_token = jsonrspp['Purchase']['AuthToken']
        self.log("Auth token: " + str(jsonrspp['Purchase']['AuthToken']))
        dt_custom_data = base64.b64encode("{\"userId\":\"" + self.GOcustomerId + "\",\"sessionId\":\"" + PlayerSessionId + "\",\"merchant\":\"hboeurope\"}")

        li = xbmcgui.ListItem(path=MediaUrl)
        license_headers = 'dt-custom-data=' + dt_custom_data + '&x-dt-auth-token=' + x_dt_auth_token + '&Origin=' + self.API_HOST_ORIGIN + '&Content-Type='
        license_key = self.LICENSE_SERVER + '|' + license_headers + '|R{SSM}|JBlicense'
        self.log("Licence key: " + str(license_key))
        protocol = 'ism'
        drm = 'com.widevine.alpha'
        is_helper = inputstreamhelper.Helper(protocol, drm=drm)
        is_helper.check_inputstream()
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', protocol)
        li.setProperty('inputstream.adaptive.license_type', drm)
        li.setProperty('inputstream.adaptive.license_data', 'ZmtqM2xqYVNkZmFsa3Izag==')
        li.setProperty('inputstream.adaptive.license_key', license_key)
        self.log("Play url: " + str(li))
        xbmcplugin.setResolvedUrl(self.handle, True, li)

    def addLink(self, title, mode):
        self.log("Adding Link: " + str(title) + " MODE: " + str(mode))
        cid = title['ObjectUrl'].rsplit('/', 2)[1]

        plot = ""
        name = ""
        media_type = "movie"
        if title['ContentType'] == 1:  # 1=MOVIE/EXTRAS, 2=SERIES(serial), 3=SERIES(episode)
            name = title['Name'].encode('utf-8', 'ignore')
            if self.force_original_names:
                name = title['OriginalName'].encode('utf-8', 'ignore')
            filename = title['OriginalName'].encode('utf-8', 'ignore') + " (" + str(title['ProductionYear']) + ")"
            if self.force_scraper_names:
                name = filename
            plot = title['Abstract'].encode('utf-8', 'ignore')
            if 'AvailabilityTo' in title:
                if title['AvailabilityTo'] is not None:
                    plot = plot + ' ' + self.LB_FILM_UNTILL + ' ' + title['AvailabilityTo'].encode('utf-8', 'ignore')
        elif title['ContentType'] == 3:
            media_type = "episode"
            name = title['SeriesName'].encode('utf-8', 'ignore') + " - " + str(
                title['SeasonIndex']) + " " + self.LB_SEASON + ", " + self.LB_EPISODE + " " + str(title['Index'])
            if self.force_original_names:
                name = title['OriginalName'].encode('utf-8', 'ignore')
            filename = title['Tracking']['ShowName'].encode('utf-8', 'ignore') + " - S" + str(
                title['Tracking']['SeasonNumber']) + "E" + str(title['Tracking']['EpisodeNumber'])
            if self.force_scraper_names:
                name = filename
            plot = title['Abstract'].encode('utf-8', 'ignore')
            if 'AvailabilityTo' in title:
                plot = plot + ' ' + self.LB_EPISODE_UNTILL + ' ' + title['AvailabilityTo'].encode('utf-8', 'ignore')

        u = self.base_url + "?url=" + urllib.quote_plus(title['ObjectUrl']) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(filename) + "&cid=" + cid + "&thumbnail=" + title['BackgroundUrl']

        liz = xbmcgui.ListItem(name, iconImage=title['BackgroundUrl'], thumbnailImage=title['BackgroundUrl'])
        liz.setArt({'thumb': title['BackgroundUrl'], 'poster': title['BackgroundUrl'], 'banner': title['BackgroundUrl'],
                    'fanart': title['BackgroundUrl']})
        liz.setInfo(type="Video",
                    infoLabels={"mediatype": media_type, "episode": title['Tracking']['EpisodeNumber'],
                                "season": title['Tracking']['SeasonNumber'],
                                "tvshowtitle": title['Tracking']['ShowName'], "plot": plot,
                                "mpaa": str(title['AgeRating']) + '+', "rating": title['ImdbRate'],
                                "cast": [title['Cast'].split(', ')][0], "director": title['Director'],
                                "writer": title['Writer'], "duration": title['Duration'], "genre": title['Genre'],
                                "title": name, "originaltitle": title['OriginalName'],
                                "year": title['ProductionYear']})
        liz.addStreamInfo('video', {'width': 1920, 'height': 1080})
        liz.addStreamInfo('video', {'aspect': 1.78, 'codec': 'h264'})
        liz.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        liz.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=u, listitem=liz, isFolder=False)


    def addDir(self, item, mode, media_type):
        self.log("Adding Dir: " + str(item) + " MODE: " + str(mode))
        u = self.base_url + "?url=" + urllib.quote_plus(item['ObjectUrl']) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(item['OriginalName'].encode('utf-8', 'ignore') + " (" + str(item['ProductionYear']) + ")")
        liz = xbmcgui.ListItem(item['Name'].encode('utf-8', 'ignore'), iconImage=item['BackgroundUrl'], thumbnailImage=item['BackgroundUrl'])
        liz.setArt({'thumb': item['BackgroundUrl'], 'poster': item['BackgroundUrl'], 'banner': item['BackgroundUrl'],
                    'fanart': item['BackgroundUrl']})
        liz.setInfo(type="Video", infoLabels={"mediatype": media_type, "season": item['Tracking']['SeasonNumber'],
                                              "tvshowtitle": item['Tracking']['ShowName'],
                                              "title": item['Name'].encode('utf-8', 'ignore'),
                                              "Plot": item['Abstract'].encode('utf-8', 'ignore')})
        liz.setProperty('isPlayable', "false")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=u, listitem=liz, isFolder=True)


    def addCat(self, name, url, icon, mode):
        self.log("Adding Cat: " + str(name) + "," + str(url) + "," + str(icon) + " MODE: " + str(mode))
        u = self.base_url + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
        liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        liz.setArt({'fanart': self.resources + "fanart.jpg"})
        liz.setInfo(type="Video", infoLabels={"Title": name})
        liz.setProperty('isPlayable', "false")
        xbmcplugin.addDirectoryItem(handle=self.handle, url=u, listitem=liz, isFolder=True)


