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
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                             QNetworkRequest, QNetworkProxy)
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QValidator, QIntValidator

import hmac, hashlib, json

from settings import Settings
from ui_proxysettingdialog import Ui_ProxySettingDialog

class CnAlibabaOpen(QObject):
    pInstance = None
    openApiBaseHttpUrl = "http://gw.open.1688.com/openapi/"
    openApiBaseHttpsUrl = "https://gw.open.1688.com/openapi/"
    openApiProtocol = "param2/"
    openApiNamespace = "cn.alibaba.open/"
    openApiVersion2 = {
        'trade.order.list.get'
    }
    appKey = "4083300"
    appSignature = "k7hhlL99gf"
    
    openApiResponse = pyqtSignal(dict)
    openApiResponseException = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(CnAlibabaOpen, self).__init__(parent)
        
        self.settings = Settings.instance()
        
        self.request = QNetworkRequest()
        self.accessManager = QNetworkAccessManager(self)
        self.accessManager.setProxy(QNetworkProxy(QNetworkProxy.HttpProxy, '127.0.0.1', 8087))
        self.accessManager.finished.connect(self.finished)
        self.accessManager.sslErrors.connect(self.sslErrors)
        
    @classmethod
    def instance(cls):
        if cls.pInstance is None:
            cls.pInstance = cls()
        return cls.pInstance
    
    def get(self):
        if self.settings.http_proxy_enabled:
            self.accessManager.setProxy(QNetworkProxy(QNetworkProxy.HttpProxy,
                                                      self.settings.http_proxy,
                                                      int(self.settings.http_proxy_port),
                                                      self.settings.http_proxy_username,
                                                      self.settings.http_proxy_password))
        else:
            self.accessManager.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        
        return self.accessManager.get(self.request)
    
    def openApiVersion(self, openApiName):
        return '2/' if openApiName in self.openApiVersion2 else '1/'
            
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
        self.get()
        
        
    def accessTokenRequest(self, openApiParam = dict()):
        url = QUrl(
            self.openApiBaseHttpsUrl + self.openApiProtocol + '1/system.oauth2/getToken/' + self.appKey)
        query = QUrlQuery()
        query.addQueryItem('grant_type', 'refresh_token')
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('client_secret', self.appSignature)
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        url.setQuery(query)
        self.request.setUrl(url)
        self.get()
        
    def refreshTokenRequest(self, openApiParam = dict()):
        url = QUrl(
            self.openApiBaseHttpsUrl + self.openApiProtocol + self.openApiVersion(openApiName) + 'system.oauth2/postponeToken/' + self.appKey)
        query = QUrlQuery()
        query.addQueryItem('client_id', self.appKey)
        query.addQueryItem('client_secret', self.appSignature)
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        url.setQuery(query)
        self.request.setUrl(url)
        self.get()
        
    def openApiSignature(self, openApiName, openApiParam):
        urlPath = self.openApiProtocol + self.openApiVersion(openApiName) + self.openApiNamespace + openApiName + '/' + self.appKey
        params = []
        for key in openApiParam.keys():
            params.append(key + openApiParam.get(key))
        params = sorted(params)
        urlPath += "".join(params)
        return hmac.new(bytearray(self.appSignature, 'utf-8'),
                        bytearray(urlPath, 'utf-8'), 
                        digestmod=hashlib.sha1).hexdigest().upper()
    
    def openApiRequest(self, openApiName, openApiParam = dict()):   
        url = QUrl(
            self.openApiBaseHttpUrl + self.openApiProtocol + self.openApiVersion(openApiName) + self.openApiNamespace + openApiName + '/' + self.appKey)
        query = QUrlQuery()
        for key in openApiParam.keys():
            query.addQueryItem(key, openApiParam.get(key))
        query.addQueryItem("_aop_signature", self.openApiSignature(openApiName, openApiParam))
        url.setQuery(query)
        url = QUrl(url.toEncoded().toPercentEncoding(':/?&=%').data().decode('utf-8'))
        self.request.setUrl(url)
        self.reply = self.get()
        self.reply.error.connect(self.replyError)

    def finished(self, reply):
        response = reply.readAll()
        if len(response) == 0:
            self.openApiResponseException.emit('A network communication error occurred during the open api request: response length is 0')
            return
        
        jsonDecode = json.loads(response.data().decode('utf-8'))
        if 'exception' in jsonDecode:
            self.openApiResponseException.emit(jsonDecode.get('exception'))
        else:
            self.openApiResponse.emit(jsonDecode)

    def sslErrors(self, reply, errors):
        self.openApiResponseException.emit(str(errors))
    
    def replyError(self, code):
        self.openApiResponseException.emit('A network communication error occurred during the open api request: error code {}'.format(code))


class CnAlibabaProxySettingDialog(QDialog):
    def __init__(self, parent=None):
        super(CnAlibabaProxySettingDialog, self).__init__(parent)
        self.ui = Ui_ProxySettingDialog()
        self.ui.setupUi(self)
        self.ui.httpProxyPortLineEdit.setValidator(QIntValidator(0, 65535, self))
        self.settings = Settings.instance()
        self.ui.proxyGroupBox.setChecked(self.settings.http_proxy_enabled)
        self.ui.httpProxyLineEdit.setText(self.settings.http_proxy)
        self.ui.httpProxyPortLineEdit.setText(self.settings.http_proxy_port)
        self.ui.usernameLineEdit.setText(self.settings.http_proxy_username)
        self.ui.passwordLineEdit.setText(self.settings.http_proxy_password)
    
    def save(self):
        self.settings.http_proxy_enabled = self.ui.proxyGroupBox.isChecked()
        self.settings.http_proxy = self.ui.httpProxyLineEdit.text()
        self.settings.http_proxy_port = self.ui.httpProxyPortLineEdit.text()
        self.settings.http_proxy_username = self.ui.usernameLineEdit.text()
        self.settings.http_proxy_password = self.ui.passwordLineEdit.text()
