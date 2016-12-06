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

from datetime import datetime, timedelta

from PyQt5.QtCore import (Qt, QCoreApplication, QTranslator, QDate,
                          QDateTime, QTimer, QProcess)
from PyQt5.QtGui import QIcon, QIntValidator, QDesktopServices
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QMainWindow,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)

import alixixi_rc

from ui_authorizedialog import Ui_AuthorizeDialog
from ui_orderlistgetdialog import Ui_OrderListGetDialog
from ui_alixixi import Ui_Alixixi
from settings import Settings
from cnalibabaopen import CnAlibabaOpen, CnAlibabaProxySettingDialog
from orderlist import *
from taobaoassistant import *
from sales import *

_translate = QCoreApplication.translate

class RefreshAccessTokenDialog(QDialog):
    def __init__(self, parent=None):
        super(RefreshAccessTokenDialog, self).__init__(parent)
        self.setWindowTitle(_translate("RefreshAccessTokenDialog", "Refresh Access Token"))
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
            self.settings.access_token_expires_in = datetime.now() + timedelta(seconds=int(response['expires_in']))
            self.cnAlibabaOpen.openApiResponse.disconnect(self.responseAccessToken)
            self.accept()
        else:
            QMessageBox.warning(self, 'Open Api Response Exception', response.get('error') + ': ' + response.get('error_description'))

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
            self.settings.access_token_expires_in = datetime.now() + timedelta(seconds=int(response['expires_in']))
            self.accept()
        else:
            QMessageBox.warning(self, 'Open Api Response Exception', response.get('error') + ': ' + response.get('error_description'))
            self.reject()

def refreshAccessToken(func):
    def failed(*args, **kwargs):
        pass
    
    def wrapper(*args, **kwargs):
        settings = Settings.instance()
        access_token_expires_in = settings.access_token_expires_in
        if access_token_expires_in < datetime.now() + timedelta(hours=2):
            loginId = settings.resource_owner
            if len(loginId) > 0:
                dialog = RefreshAccessTokenDialog()
                if dialog.exec() == QDialog.Rejected:
                    return failed(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

class Alixixi(QMainWindow):
    def __init__(self, parent=None):
        super(Alixixi, self).__init__(parent)
        self.ui = Ui_Alixixi()
        self.ui.setupUi(self)
        
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponseException.connect(self.openApiResponseException)
        
        self.settings = Settings.instance()
        self.settings.resource_owner_changed.connect(self.ui.loginIdLineEdit.setText)
        loginId = self.settings.resource_owner
        if len(loginId) > 0:
            self.ui.loginIdLineEdit.setText(self.settings.resource_owner)
        
        self.ui.aliOrderReviewPushButton.released.connect(self.aliOrderListReview)
        
        self.ui.tbAssistantOpenPushButton.released.connect(self.tbAssistantOpen)
        self.ui.tbOrderLogisticsUpdatePushButton.released.connect(self.tbOrderListLogisticsUpdate)
        self.ui.tbOrderReviewPushButton.released.connect(self.tbOrderListReview)
        
        self.addMenus()
    
    def addMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu(_translate('Alixixi', 'File'))
        fileMenu.addAction(_translate('Alixixi', 'Close'), QCoreApplication.instance().quit)
        
        setttingsMenu = menuBar.addMenu(_translate('Alixixi', 'Setting'))
        setttingsMenu.addAction(_translate('Alixixi', 'Authorize'), self.authorizeRequest)
        setttingsMenu.addAction(_translate('Alixixi', 'Proxy'), self.proxySetting)
        setttingsMenu.addAction(_translate('Alixixi', 'Taobao Assistant'), self.taobaoAssistantSetting)
        
        aliOrderMenu = menuBar.addMenu(_translate('Alixixi', 'Ali Order'))
        aliOrderUpdateMenu = aliOrderMenu.addMenu(_translate('Alixixi', 'Update'))
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'Today'), self.todayOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last 2 Days'), self.last2DaysOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last 3 Days'), self.last3DaysOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last 5 Days'), self.last5DaysOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last Week'), self.lastWeekOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last 2 Weeks'), self.last2WeeksOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'The Last Month'), self.lastMonthOrderListGet)
        aliOrderUpdateMenu.addAction(_translate('Alixixi', 'Custom Date Range'), self.customDateRangeOrderListGet)
        aliOrderMenu.addAction(_translate('Alixixi', 'Review'), self.aliOrderListReview)
        
        salePerformanceMenu = menuBar.addMenu(_translate('Alixixi', 'Sales'))
        salePerformanceMenu.addAction(_translate('Alixixi', 'Reporting'), self.saleReportReview)
        
    def openApiResponseException(self, warning):
        QMessageBox.warning(self, 'Open Api Response Exception', warning)
        
    def authorizeRequest(self):
        QDesktopServices.openUrl(self.cnAlibabaOpen.openApiAuthorizeRequest())
        dialog = AuthorizeDialog(self)
        dialog.exec()
        
    def proxySetting(self):
        dialog = CnAlibabaProxySettingDialog(self)
        if dialog.exec() == QDialog.Accepted:
            dialog.save()
    
    def taobaoAssistantSetting(self):
        dialog = TaobaoAssistantSettingDialog(self)
        if dialog.exec() == QDialog.Accepted:
            dialog.save()
    
    def todayOrderListGet(self):
        self.aliOrderListGetRequest()
    
    def last2DaysOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-1))
    
    def last3DaysOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-2))
    
    def last5DaysOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-4))
    
    def lastWeekOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-6))
    
    def last2WeeksOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-13))
    
    def lastMonthOrderListGet(self):
        self.aliOrderListGetRequest(QDate.currentDate().addDays(-30))
    
    @refreshAccessToken
    def customDateRangeOrderListGet(self):
        dialog = OrderListGetDialog(QDate(self.settings.ali_order_last_update_time.date()), \
                                    QDate.currentDate(), OrderListGetDialog.Mode.custom)
        dialog.exec()
    
    @refreshAccessToken
    def aliOrderListGetRequest(self, createStartTime = QDate.currentDate(), createEndTime = QDate.currentDate()):
        dialog = OrderListGetDialog(createStartTime, createEndTime)
        if dialog.exec() == QDialog.Accepted:
            self.aliOrderListReview()
    
    @refreshAccessToken
    def aliOrderListAutoUpdate(self, second):
        delta = datetime.today() - self.settings.ali_order_last_update_time
        if delta.total_seconds() > second:
            button = QMessageBox.question(self, _translate('Alixixi', 'Ali Order'),
                                          _translate('Alixixi', 'Automatically update ali order?'))
            if button == QMessageBox.Yes:
                createStartTime = QDate(self.settings.ali_order_last_update_time.date())
                createEndTime = QDate.currentDate()
                if createStartTime.addMonths(1) < createEndTime:
                    createStartTime = createEndTime.addDays(-28)
                dialog = OrderListGetDialog(createStartTime, createEndTime, OrderListGetDialog.Mode.auto)
                dialog.exec()
    
    def aliOrderListReview(self):
        self.aliOrderListAutoUpdate(60 * 60)
        dialog = OrderListReviewDialog(self)
        dialog.exec()
    
    def saleReportReview(self):
        dialog = SalesReportingDialog(self)
        dialog.exec()
    
    @taobaoAssistantInstallPathCheck
    @taobaoAssistantWorkbenchIsRunning
    def tbAssistantOpen(self):
        taobaoAssistantWorkbenchLaunch()
    
    @taobaoAssistantInstallPathCheck
    @taobaoAssistantWorkbenchIsRunning
    def tbOrderListLogisticsUpdate(self):
        self.aliOrderListAutoUpdate(30)
        dialog = TaobaoOrderLogisticsUpdateDialog(self)
        dialog.exec()
    
    @taobaoAssistantInstallPathCheck
    @taobaoAssistantWorkbenchIsRunning
    def tbOrderListReview(self):
        dialog = TaobaoOrderListReviewDialog(self)
        dialog.exec()

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/images/alixixi.ico'))
    translator = QTranslator(app)
    translator.load('alixixi_zh_CN')
    app.installTranslator(translator)
    alixixi = Alixixi()
    alixixi.show()
    sys.exit(app.exec_())
