#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2016 xlongfeng<xlongfeng@126.com>.
## All rights reserved.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################


from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QUrlQuery
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

import hmac, hashlib, json

class CnAlibabaOpen(QObject):
    openApiBaseHttpUrl = "http://gw.open.1688.com/openapi/"
    openApiBaseHttpsUrl = "https://gw.open.1688.com/openapi/"
    openApiProtocol = "param2/"
    openApiVersion = "1/"
    openApiNamespace = "cn.alibaba.open/"
    appKey = "6972191"
    appSignature = "teidQsuKyUiv"
    refreshToken = "74831383-be8c-473e-898b-e6a90cd1f7e6"
    accessToken = "5ce190b5-b98f-433d-947f-06042783a16d"
    
    openApiResponse = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super(CnAlibabaOpen, self).__init__(parent)

        self.networkSession = None

        self.request = QNetworkRequest()
        self.accessManager = QNetworkAccessManager(self)
        self.accessManager.finished.connect(self.finished)
        self.accessManager.sslErrors.connect(self.sslErrors)
            
    def openApiSignature(self, openApiName, openApiParam):
        urlPath = self.openApiProtocol + self.openApiVersion + self.openApiNamespace + openApiName + '/' + self.appKey
        params = []
        for key in openApiParam.keys():
            params.append(key + openApiParam.get(key))
        params = sorted(params)
        urlPath += "".join(params)
        return hmac.new(bytearray(self.appSignature, 'utf-8'),
                        bytearray(urlPath, 'utf-8'), 
                        digestmod=hashlib.sha1).hexdigest().upper()
    
    def openApiAuthorizeSignature(self, query):
        urlPath = ''
        items = query.queryItems()
        params = []
        for pair in items:
            params.append(pair[0] + pair[1])
        params = sorted(params)
        return hmac.new(bytearray(self.appSignature, 'utf-8'),
                        bytearray("".join(params), 'utf-8'), 
                        digestmod=hashlib.sha1).hexdigest().upper()
    
    def openApiAuthorizeRequest(self):
        url = QUrl('http://gw.open.1688.com/auth/authorize.htm')
        query = QUrlQuery()
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('site', 'china')
        query.addQueryItem('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob')
        query.addQueryItem('_aop_signature', self.openApiAuthorizeSignature(query))
        url.setQuery(query)
        return url
    
    def tokenRequest(self, openApiParam = dict()):
        url = QUrl('https://gw.open.1688.com/openapi/http/1/system.oauth2/getToken/' + self.appKey)
        query = QUrlQuery()
        query.addQueryItem('grant_type', 'authorization_code')
        query.addQueryItem('need_refresh_token', 'true')
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('client_secret', self.appSignature)
        query.addQueryItem('redirect_uri', 'urn:ietf:wg:oauth:2.0:oob')
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        url.setQuery(query)
        self.request.setUrl(url)
        self.accessManager.get(self.request)
    
    def openApiRequest(self, openApiName, openApiParam = dict()):   
        url = QUrl(
            self.openApiBaseHttpUrl + self.openApiProtocol + self.openApiVersion + self.openApiNamespace + openApiName + '/' + self.appKey)
        query = QUrlQuery()
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        query.addQueryItem("_aop_signature", self.openApiSignature(openApiName, openApiParam))
        url.setQuery(query)
        self.request.setUrl(url)
        self.accessManager.get(self.request)
        
    def accessTokenRequest(self, openApiParam = dict()):
        url = QUrl(
            self.openApiBaseHttpsUrl + self.openApiProtocol + self.openApiVersion + 'system.oauth2/getToken/' + self.appKey)
        query = QUrlQuery()
        query.addQueryItem('grant_type', 'refresh_token')
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('client_secret', self.appSignature)
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        url.setQuery(query)
        self.request.setUrl(url)
        self.accessManager.get(self.request)
        
    def refreshTokenRequest(self, openApiParam = dict()):
        url = QUrl(
            self.openApiBaseHttpsUrl + self.openApiProtocol + self.openApiVersion + 'system.oauth2/postponeToken/' + self.appKey)
        query = QUrlQuery()
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('client_secret', self.appSignature)
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        url.setQuery(query)
        self.request.setUrl(url)
        self.accessManager.get(self.request)

    def finished(self, reply):
        response = reply.readAll()
        jsonDecode = json.loads(response.data().decode('utf-8'))
        print(jsonDecode)
        if 'exception' in jsonDecode:
            print(jsonDecode.get('exception'))
        else:
            self.openApiResponse.emit(jsonDecode)

    def sslErrors(self, reply, errors):
        pass