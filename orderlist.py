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


from PyQt5.QtCore import Qt, QCoreApplication, QDate, QDateTime, QTimer
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import json
from jinja2 import Environment, FileSystemLoader

from ui_orderlistgetdialog import Ui_OrderListGetDialog
from ui_orderlistreviewdialog import Ui_OrderListReviewDialog
from settings import Settings
from cnalibabaopen import *

_translate = QCoreApplication.translate

class OrderListGetDialog(QDialog):
    def __init__(self, createStartTime, createEndTime, parent=None):
        super(OrderListGetDialog, self).__init__(parent)
        self.ui = Ui_OrderListGetDialog()
        self.ui.setupUi(self)
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        
        self.settings = Settings(self)
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponse.connect(self.orderListGetReponse)
        self.cnAlibabaOpen.openApiResponse.connect(self.orderDetailGetResponse)
        
        # prepare to get order list
        self.orderList = dict()
        self.orderDetailIdList = []
        self.createStartTime = createStartTime
        self.createEndTime = createEndTime
        self.totalCount = 0
        self.count = 0
        self.page = 1
        self.orderModelId = ''
        QTimer.singleShot(100, self.orderListGetRequest)
        
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
            with open('orderlist.json', 'w', encoding='utf-8') as f:
                jsonEncode = json.dump(self.orderList, f)
            QMessageBox.information(self, _translate('OrderListGetDialog', 'Order List Get'), _translate('OrderListGetDialog', 'Query order list complete'))
            self.accept()
        
    def orderDetailGetRequest(self):
        param = dict()
        param['access_token'] = self.settings.access_token
        param['id'] = str(self.orderModelId)
        param['needOrderEntries'] = 'false'
        param['needInvoiceInfo'] = 'false'
        self.cnAlibabaOpen.openApiRequest('trade.order.detail.get', param)
        
    def orderListGetRequest(self):
        param = dict()
        param['access_token'] = self.settings.access_token
        param['createStartTime'] = self.createStartTime
        param['createEndTime'] = self.createEndTime
        param['buyerMemberId'] = self.settings.memberId
        param['page'] = str(self.page)
        param['pageSize'] = '10'
        self.cnAlibabaOpen.openApiRequest('trade.order.list.get', param)
        
    def dateTimeConvert(self, dateTime):
        return QDateTime.fromString(dateTime, 'yyyyMMddhhmmsszzz+0800').toString('yyyy-MM-dd hh:mm:ss')
        
    def currencyUnitConvert(self, price):
        return float(price / 100.0)
        
    def orderListAppend(self, modelList):
        self.orderDetailIdList = []
        for orderModel in modelList:
            id = orderModel['id']
            self.orderDetailIdList.append(id)
            self.orderList[id] = dict()
            self.orderList[id]['id'] = id
            self.orderList[id]['status'] = _translate('OrderListReview', orderModel['status'])
            self.orderList[id]['gmtCreate'] = self.dateTimeConvert(orderModel['gmtCreate'])
            self.orderList[id]['sumProductPayment'] = self.currencyUnitConvert(orderModel['sumProductPayment'])
            self.orderList[id]['carriage'] = self.currencyUnitConvert(orderModel['carriage'])
            self.orderList[id]['sumPayment'] = self.currencyUnitConvert(orderModel['sumPayment'])
            self.orderList[id]['orderEntries'] = []
            for orderEntryModel in orderModel['orderEntries']:
                orderEntry = dict()
                orderEntry['productName'] = orderEntryModel['productName']
                specInfo = []
                for specItems in orderEntryModel['specInfoModel']['specItems']:
                    specInfo.append({'specName': specItems['specName'], 'specValue': specItems['specValue']})
                orderEntry['specInfo'] = specInfo
                orderEntry['price'] = self.currencyUnitConvert(orderEntryModel['price'])
                orderEntry['quantity'] = orderEntryModel['quantity']
                orderEntry['promotionsFee'] = self.currencyUnitConvert(orderEntryModel['promotionsFee'])
                orderEntry['actualPayFee'] = self.currencyUnitConvert(orderEntryModel['actualPayFee'])
                orderEntry['mainSummImageUrl'] = orderEntryModel['mainSummImageUrl']
                orderEntry['entryStatus'] = _translate('OrderListReview', orderEntryModel['entryStatus'])
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
                QMessageBox.information(self, _translate('OrderListGetDialog', 'Order List Get'), _translate('OrderListGetDialog', 'Empty order list'))
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
                    'gmtSend': self.dateTimeConvert(logisticsOrderModel['gmtSend'])
                })
            self.orderList[id]['logisticsOrderList'] = logisticsOrderList
        
        self.orderDetailGetNext()
        
class OrderListReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(OrderListReviewDialog, self).__init__(parent)
        self.ui = Ui_OrderListReviewDialog()
        self.ui.setupUi(self)
        self.ui.label.setBuddy(self.ui.findTextLineEdit)
        self.resize(1050, 600)
        self.retranslate()
        
        self.ui.nextPushButton.clicked.connect(self.searchNext)
        self.ui.prevPushButton.clicked.connect(self.searchPrev)
        self.ui.clearPushButton.clicked.connect(self.searchClear)
        
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.linkClicked.connect(self.linkClicked)
        self.ui.webView.setHtml(_translate('OrderListReview', 'Loading, wait a monent ...'))
        QTimer.singleShot(100, self.setHtml)
        
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
        
    def searchNext(self, options = QWebPage.FindWrapsAroundDocument):
        findText = self.ui.findTextLineEdit.text().strip()
        if len(findText) > 0:
            if self.ui.webView.findText(findText, QWebPage.FindWrapsAroundDocument) == False:
                self.ui.webView.findText('', QWebPage.FindWrapsAroundDocument)
    
    def searchPrev(self, options = QWebPage.FindBackward | QWebPage.FindWrapsAroundDocument):
        self.searchNext(options)
    
    def searchClear(self):
        self.ui.findTextLineEdit.setText('')
        self.ui.webView.findText('')
        
    def linkClicked(self, url):
        QDesktopServices.openUrl(url)
        
    def setHtml(self):
        with open('orderlist.json', 'r', encoding='utf-8') as f:
            jsonDecode = json.load(f)
            
            orderList = jsonDecode.values()
            orderList = sorted(orderList, key=lambda d: d['gmtCreate'], reverse=True)
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('orderlist.html')
            self.ui.webView.setHtml(template.render(orderList = orderList))