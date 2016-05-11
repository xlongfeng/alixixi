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


from PyQt5.QtCore import Qt, QCoreApplication, QTranslator, QDate
from PyQt5.QtGui import QIntValidator, QDesktopServices
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QMainWindow,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)

from ui_authorizedialog import Ui_AuthorizeDialog
from ui_orderlistgetdialog import Ui_OrderListGetDialog
from ui_alixixi import Ui_Alixixi
from settings import Settings
from cnalibabaopen import CnAlibabaOpen

_translate =QCoreApplication.translate
settings = None
cnalibabaopen = None

class RefreshTokenDialog(QDialog):
    def __init__(self, parent=None):
        super(RefreshTokenDialog, self).__init__(parent)
        self.ui = Ui_RefreshTokenDialog()
        self.ui.setupUi(self)
        
        self.ui.updatePushButton.clicked.connect(self.requestAccessToken)
        
        cnAlibabaOpen.openApiResponse.connect(self.responseAccessToken)
        
    def requestAccessToken(self):
        if len(self.ui.refreshTokenLineEdit.text()) > 0:
            cnAlibabaOpen.accessTokenRequest({'refresh_token': self.ui.refreshTokenLineEdit.text()})
    
    def requestRefreshToken(self):
        cnAlibabaOpen.refreshTokenRequest({'access_token': settings.access_token, 'refresh_token': settings.refresh_token})
    
    def responseAccessToken(self, response):
        if 'access_token' in response:
            print(response.get('access_token'))
            print(response.get('aliId'))
            print(response.get('expires_in'))
            print(response.get('memberId'))
            print(response.get('resource_owner'))
        else:
            print(response.get('error') + ': ' + response.get('error_description'))
    
    def responseRefreshToken(self, response):
        pass
    
class AuthorizeDialog(QDialog):
    def __init__(self, parent=None):
        super(AuthorizeDialog, self).__init__(parent)
        self.ui = Ui_AuthorizeDialog()
        self.ui.setupUi(self)
        self.ui.continuePushButton.clicked.connect(self.requestToken)
        
        cnAlibabaOpen.openApiResponse.connect(self.responseToken)
        
    def requestToken(self):
        if len(self.ui.authorizeCodeLineEdit.text()) > 0:
            cnAlibabaOpen.tokenRequest({'code': self.ui.authorizeCodeLineEdit.text()})
    
    def responseToken(self, response):
        if 'access_token' in response:
            settings.access_token = response.get('access_token')
            settings.aliId = response.get('aliId')
            settings.expires_in = response.get('expires_in')
            settings.memberId = response.get('memberId')
            settings.refresh_token = response.get('refresh_token')
            settings.refresh_token_timeout = response.get('refresh_token_timeout')
            settings.resource_owner = response.get('resource_owner')
            self.accept()
        else:
            print(response.get('error') + ': ' + response.get('error_description'))
            self.reject()
            
class OrderListGetDialog(QDialog):
    def __init__(self, createStartTime, createEndTime, parent=None):
        super(OrderListGetDialog, self).__init__(parent)
        self.ui = Ui_OrderListGetDialog()
        self.ui.setupUi(self)
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        
        self.retranslate()
        
        cnAlibabaOpen.openApiResponse.connect(self.orderListGetReponse)
        cnAlibabaOpen.openApiResponse.connect(self.orderDetailGetResponse)
        
        # prepare to get order list
        self.orderList = dict()
        self.orderDetailIdList = []        
        self.createStartTime = createStartTime
        self.createEndTime = createEndTime
        self.totalCount = 0
        self.count = 0
        self.page = 1
        self.orderModelId = ''
        self.orderListGetRequest()
        
    def retranslate(self):
        _translate('OrderListReview', 'CANCEL')
        _translate('OrderListReview', 'SUCCESS')
        _translate('OrderListReview', 'WAIT_BUYER_PAY')
        _translate('OrderListReview', 'WAIT_SELLER_SEND')
        _translate('OrderListReview', 'WAIT_BUYER_RECEIVE')
        _translate('OrderListReview', 'WAIT_SELLER_ACT')
        _translate('OrderListReview', 'WAIT_BUYER_CONFIRM_ACTION')
        _translate('OrderListReview', 'WAIT_SELLER_PUSH')
        _translate('OrderListReview', 'WAIT_LOGISTICS_TAKE_IN')
        _translate('OrderListReview', 'WAIT_BUYER_SIGN')
        _translate('OrderListReview', 'SIGN_IN_SUCCESS')
        _translate('OrderListReview', 'SIGN_IN_FAILED')
        
    def orderDetailGetNext(self):
        if len(self.orderDetailIdList) > 0:
            # get next order detial
            self.count += 1
            self.ui.progressBar.setValue(self.count)
            self.orderModelId = self.orderDetailIdList.pop()
            self.orderDetailGetRequest()
        elif self.count < self.totalCount:
            # get next order list
            self.page += 1
            self.orderListGetRequest()
        else:
            # task done
            print(self.orderList)
            with open('orderlist.json', 'w', encoding='utf-8') as f:
                f.write(str(self.orderList))
            QMessageBox.information(self, _translate('OrderListGetDialog', 'Order List Get'), _translate('OrderListGetDialog', 'Query order list complete'))
            self.accept()
        
    def orderDetailGetRequest(self):
        param = dict()
        param['access_token'] = settings.access_token
        param['id'] = str(self.orderModelId)
        param['needOrderEntries'] = 'false'
        param['needInvoiceInfo'] = 'false'
        cnAlibabaOpen.openApiRequest('trade.order.detail.get', param)
        
    def orderListGetRequest(self):
        param = dict()
        param['access_token'] = settings.access_token
        param['createStartTime'] = self.createStartTime
        param['createEndTime'] = self.createEndTime
        param['buyerMemberId'] = settings.memberId
        param['page'] = str(self.page)
        param['pageSize'] = '10'
        cnAlibabaOpen.openApiRequest('trade.order.list.get', param)
        
    def orderListAppend(self, modelList):
        self.orderDetailIdList = []
        for orderModel in modelList:
            id = orderModel['id']
            self.orderDetailIdList.append(id)
            self.orderList[id] = dict()
            self.orderList[id]['status'] = orderModel['status']
            self.orderList[id]['sumProductPayment'] = orderModel['sumProductPayment']
            self.orderList[id]['carriage'] = orderModel['carriage']
            self.orderList[id]['sumPayment'] = orderModel['sumPayment']
            self.orderList[id]['orderEntries'] = []
            for orderEntryModel in orderModel['orderEntries']:
                orderEntry = dict()
                orderEntry['productName'] = orderEntryModel['productName']
                specInfo = []
                for specItems in orderEntryModel['specInfoModel']['specItems']:
                    specInfo.append({specItems['specName']: specItems['specValue']})
                orderEntry['specInfo'] = specInfo
                orderEntry['price'] = orderEntryModel['price']
                orderEntry['quantity'] = orderEntryModel['quantity']
                orderEntry['promotionsFee'] = orderEntryModel['promotionsFee']
                orderEntry['productName'] = orderEntryModel['productName']
                self.orderList[id]['orderEntries'].append(orderEntry)
                
        # prepare to get order detail
        self.orderDetailGetNext()
        
    def orderListGetReponse(self, response):
        if 'orderListResult' not in response:
            return
        orderListResult = response['orderListResult']
        if self.totalCount == 0:
            # first call
            self.totalCount = orderListResult['totalCount']
            if self.totalCount == 0:
                self.reject()
                return
            else:
                self.ui.progressBar.setRange(0, self.totalCount)
        self.orderListAppend(orderListResult['modelList'])
                
    def orderDetailGetResponse(self, response):
        if 'orderModel' not in response:
            return
        orderModel = response['orderModel']
        
        id = orderModel['id']
        self.orderList[id]['toFullName'] = orderModel['toFullName']
        self.orderList[id]['toMobile'] = orderModel['toMobile']
        self.orderList[id]['buyerPhone'] = orderModel['buyerPhone']
        self.orderList[id]['toArea'] = orderModel['toArea']
        if 'logisticsOrderList' in orderModel:
            logisticsOrderList = []
            for logisticsOrderModel in orderModel['logisticsOrderList']:
                logisticsOrderList.append({
                    'logisticsOrderNo': logisticsOrderModel['logisticsOrderNo'],
                    'companyName': logisticsOrderModel['logisticsCompany']['companyName'],
                    'logisticsBillNo': logisticsOrderModel['logisticsBillNo'],
                    'gmtLogisticsCompanySend': logisticsOrderModel['gmtLogisticsCompanySend']
                })
            self.orderList[id]['logisticsOrderList'] = logisticsOrderList
        
        self.orderDetailGetNext()
        
class Alixixi(QMainWindow):
    def __init__(self, parent=None):
        super(Alixixi, self).__init__(parent)
        self.ui = Ui_Alixixi()
        self.ui.setupUi(self)
        
        self.ui.authorizePushButton.clicked.connect(self.authorizeRequest)
        
        settings.resource_owner_changed.connect(self.ui.loginIdLineEdit.setText)
        self.ui.loginIdLineEdit.setText(settings.resource_owner)
        
        self.ui.createStartTimeDateEdit.setDate(QDate.currentDate())
        self.ui.createEndTimeDateEdit.setDate(QDate.currentDate())
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
        
    def authorizeRequest(self):
        QDesktopServices.openUrl(cnAlibabaOpen.openApiAuthorizeRequest())
        dialog = AuthorizeDialog(self)
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
        dialog.exec()
        
    def orderListReview(self):
        pass
    
    def memberGetRequest(self):
        cnAlibabaOpen.openApiResponse.connect(self.memberGetResponse)
        cnAlibabaOpen.openApiRequest('member.get', {'memberId': settings.memberId})

    def memberGetResponse(self, response):
        print(response)

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    translator = QTranslator(app)
    translator.load('alixixi_zh_CN')
    app.installTranslator(translator)
    settings = Settings(app)
    cnAlibabaOpen = CnAlibabaOpen(app)
    alixixi = Alixixi()
    alixixi.show()
    sys.exit(app.exec_())
