#!/usr/bin/env python
# -*- coding: utf-8 -*-


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


from PyQt5.QtCore import (Qt, QCoreApplication, QTranslator, QDate,
                          QDateTime, QTimer)
from PyQt5.QtGui import QIntValidator, QDesktopServices
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QMainWindow,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)

from ui_authorizedialog import Ui_AuthorizeDialog
from ui_orderlistgetdialog import Ui_OrderListGetDialog
from ui_alixixi import Ui_Alixixi
from settings import Settings
from cnalibabaopen import CnAlibabaOpen
from orderlist import OrderListGetDialog, OrderListReviewDialog

_translate = QCoreApplication.translate

class ReAuthorizeDialog(QDialog):
    def __init__(self, parent=None):
        super(ReAuthorizeDialog, self).__init__(parent)
        self.setWindowTitle(_translate("ReAuthorizeDialog", "Refresh Access Token"))
        self.resize(240, 96)
        self.settings = Settings.instance()
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponse.connect(self.responseAccessToken)
        QTimer.singleShot(100, self.requestAccessToken)
        
    def requestAccessToken(self):
        self.cnAlibabaOpen.accessTokenRequest({'refresh_token': self.settings.refresh_token})
    
    def responseAccessToken(self, response):
        if 'access_token' in response:
            self.settings.access_token = response['access_token']
            self.settings.access_token_expires_in = QDateTime.currentDateTime().addSecs(int(response['expires_in']))
            self.accept()
        else:
            print(response.get('error') + ': ' + response.get('error_description'))
    
class AuthorizeDialog(QDialog):
    def __init__(self, parent=None):
        super(AuthorizeDialog, self).__init__(parent)
        self.ui = Ui_AuthorizeDialog()
        self.ui.setupUi(self)
        self.ui.continuePushButton.clicked.connect(self.requestToken)
        
        self.settings = Settings.instance()
        
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponse.connect(self.responseToken)
        
    def requestToken(self):
        if len(self.ui.authorizeCodeLineEdit.text()) > 0:
            self.cnAlibabaOpen.tokenRequest({'code': self.ui.authorizeCodeLineEdit.text()})
    
    def responseToken(self, response):
        if 'access_token' in response:
            self.settings.access_token = response.get('access_token')
            self.settings.aliId = response.get('aliId')
            self.settings.expires_in = response.get('expires_in')
            self.settings.memberId = response.get('memberId')
            self.settings.refresh_token = response.get('refresh_token')
            self.settings.refresh_token_timeout = response.get('refresh_token_timeout')
            self.settings.resource_owner = response.get('resource_owner')
            self.settings.access_token_expires_in = QDateTime.currentDateTime().addSecs(int(response['expires_in']))
            self.accept()
        else:
            print(response.get('error') + ': ' + response.get('error_description'))
            self.reject()
    
class Alixixi(QMainWindow):
    def __init__(self, parent=None):
        super(Alixixi, self).__init__(parent)
        self.ui = Ui_Alixixi()
        self.ui.setupUi(self)
        
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponseException.connect(self.openApiResponseException)
        
        self.ui.authorizePushButton.clicked.connect(self.authorizeRequest)
        self.ui.reAuthorizePushButton.clicked.connect(self.reAuthorizeRequest)
        
        self.settings = Settings.instance()
        self.settings.resource_owner_changed.connect(self.ui.loginIdLineEdit.setText)
        loginId = self.settings.resource_owner
        if len(loginId) > 0:
            self.ui.loginIdLineEdit.setText(self.settings.resource_owner)
        else:
            self.ui.reAuthorizePushButton.setDisabled(True)
        
        self.todayRange()
        self.ui.todayPushButton.clicked.connect(self.todayRange)
        self.ui.last2DaysPushButton.clicked.connect(self.last2DaysRange)
        self.ui.last3DaysPushButton.clicked.connect(self.last3DaysRange)
        self.ui.lastWeekPushButton.clicked.connect(self.lastWeekRange)
        self.ui.last2WeeksPushButton.clicked.connect(self.last2WeeksRange)
        self.ui.lastMonthPushButton.clicked.connect(self.lastMonthRange)
        self.ui.orderListGetPushButton.clicked.connect(self.orderListGetRequest)
        self.ui.orderListReviewPushButton.clicked.connect(self.orderListReview)
        
        self.ui.memberGetPushButton.clicked.connect(self.memberGetRequest)
        self.ui.memberGetPushButton.setHidden(True)
        
        QTimer.singleShot(1000, self.refreshAccessToken)
        
    def openApiResponseException(self, warning):
        QMessageBox.warning(self, 'Open Api Response Exception', warning)
        
    def authorizeRequest(self):
        QDesktopServices.openUrl(self.cnAlibabaOpen.openApiAuthorizeRequest())
        dialog = AuthorizeDialog(self)
        dialog.exec()
        
    def reAuthorizeRequest(self):
        dialog = ReAuthorizeDialog(self)
        dialog.exec()
        
    def todayRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate())
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
        
    def last2DaysRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate().addDays(-1))
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())

    def last3DaysRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate().addDays(-2))
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
        
    def lastWeekRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate().addDays(-6))
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
        
    def last2WeeksRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate().addDays(-13))
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
        
    def lastMonthRange(self):
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate().addDays(-30))
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
        
    def orderListGetRequest(self):
        createStartTime = self.ui.createStartTimeDateEdit.date().toString('yyyyMMdd00000000+0800')
        createEndTime = self.ui.createEndTimeDateEdit.date().toString('yyyyMMdd23595900+0800')
        dialog = OrderListGetDialog(createStartTime, createEndTime, self)
        if dialog.exec() == QDialog.Accepted:
            self.orderListReview()
        
    def orderListReview(self):
        dialog = OrderListReviewDialog(self)
        dialog.exec()
    
    def memberGetRequest(self):
        self.cnAlibabaOpen.openApiResponse.connect(self.memberGetResponse)
        self.cnAlibabaOpen.openApiRequest('member.get', {'memberId': self.settings.memberId})

    def memberGetResponse(self, response):
        print(response)
        
    def refreshAccessToken(self):
        access_token_expires_in = self.settings.access_token_expires_in
        if type(access_token_expires_in) == QDateTime:
            if access_token_expires_in < QDateTime.currentDateTime().addSecs(60 * 60 * 2):
                self.reAuthorizeRequest()

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    translator = QTranslator(app)
    translator.load('alixixi_zh_CN')
    app.installTranslator(translator)
    alixixi = Alixixi()
    alixixi.show()
    sys.exit(app.exec_())
