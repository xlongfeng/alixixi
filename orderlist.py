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
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox, QDialog,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import json
from math import ceil
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, func

from ui_orderlistgetdialog import Ui_OrderListGetDialog
from ui_orderlistreviewdialog import Ui_OrderListReviewDialog
from settings import Settings
from cnalibabaopen import CnAlibabaOpen
from orm import *

_translate = QCoreApplication.translate

def translates():
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
            session.commit()
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
        
    def orderListAppend(self, modelList):
        self.orderDetailIdList = []
        for orderModel in modelList:
            orderId = orderModel['id']
            self.orderDetailIdList.append(orderId)
            orderEntries = []
            for orderEntryModel in orderModel['orderEntries']:
                orderEntry = dict()
                orderEntry['productName'] = orderEntryModel['productName']
                specInfo = []
                for specItems in orderEntryModel['specInfoModel']['specItems']:
                    specInfo.append({'specName': specItems['specName'], 'specValue': specItems['specValue']})
                orderEntry['specInfo'] = specInfo
                orderEntry['price'] = ccyUnitConvert(orderEntryModel['price'])
                orderEntry['quantity'] = orderEntryModel['quantity']
                orderEntry['promotionsFee'] = ccyUnitConvert(orderEntryModel['promotionsFee'])
                orderEntry['actualPayFee'] = ccyUnitConvert(orderEntryModel['actualPayFee'])
                orderEntry['mainSummImageUrl'] = orderEntryModel['mainSummImageUrl']
                orderEntry['entryStatus'] = _translate('OrderListReview', orderEntryModel['entryStatus'])
                orderEntries.append(orderEntry)
            
            # add a new one or update an exist one
            model = session.query(AliOrderModel).filter_by(orderId = orderId).one_or_none()
            new = False
            if not model:
                model = AliOrderModel()
                new = True
            model.carriage = ccyUnitConvert(orderModel['carriage'])
            model.gmtCreate = aliTimeToDateTime(orderModel['gmtCreate'])
            model.orderId = orderId
            model.status = _translate('OrderListReview', orderModel['status'])
            model.sumProductPayment = ccyUnitConvert(orderModel['sumProductPayment'])
            model.sumPayment = ccyUnitConvert(orderModel['sumPayment'])
            model.orderEntries = json.dumps(orderEntries)
            if new:
                session.add(model)
        
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
        orderId = orderModel['id']
        model = session.query(AliOrderModel).filter_by(orderId = orderId).one()
        model.buyerPhone = orderModel['buyerPhone']
        model.toArea = orderModel['toArea']
        model.toFullName = orderModel['toFullName']
        model.toMobile = orderModel['toMobile']
        if 'logisticsOrderList' in orderModel:
            logisticsOrderList = []
            for logisticsOrderModel in orderModel['logisticsOrderList']:
                logisticsOrderList.append({
                    'logisticsOrderNo': logisticsOrderModel['logisticsOrderNo'],
                    'companyName': logisticsOrderModel['logisticsCompany']['companyName'],
                    'logisticsBillNo': logisticsOrderModel['logisticsBillNo'],
                    'gmtSend': str(aliTimeToDateTime(logisticsOrderModel['gmtSend']))
                })
            model.logisticsOrderList = json.dumps(logisticsOrderList)
            
        self.orderDetailGetNext()
        
class OrderListReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(OrderListReviewDialog, self).__init__(parent)
        self.ui = Ui_OrderListReviewDialog()
        self.ui.setupUi(self)
        self.ui.label.setBuddy(self.ui.findTextLineEdit)
        self.resize(1050, 600)
        
        
        self.ui.firstPagePushButton.clicked.connect(self.firstPage)
        self.ui.prevPagePushButton.clicked.connect(self.prevPage)
        self.ui.nextPagePushButton.clicked.connect(self.nextPage)
        self.ui.lastPagePushButton.clicked.connect(self.lastPage)

        self.ui.nextPushButton.clicked.connect(self.searchNext)
        self.ui.prevPushButton.clicked.connect(self.searchPrev)
        self.ui.clearPushButton.clicked.connect(self.searchClear)
        
        self.ui.advancedSearchGroupBox.toggled.connect(self.advancedSearchToggled)
        self.ui.advancedSearchPushButton.clicked.connect(self.advancedSearch)
        self.ui.advancedSearchClearPushButton.clicked.connect(self.advancedSearchClear)
        
        self.advancedSearchFilter = dict()
        self.pageInfoUpdate()
        
        self.ui.webView.settings().setAttribute(QWebSettings.OfflineStorageDatabaseEnabled, True)
        self.ui.webView.settings().setAttribute(QWebSettings.OfflineWebApplicationCacheEnabled, True)
        self.ui.webView.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        self.ui.webView.settings().enablePersistentStorage()
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.linkClicked.connect(self.linkClicked)
        
        if self.totalPages == 0:
            self.setHtml()
        else:
            self.ui.webView.setHtml(_translate('OrderListReview', 'Loading, wait a monent ...'))
            QTimer.singleShot(100, self.firstPage)
            
    def queryFilter(self):
        query = session.query(AliOrderModel)
        for attr, value in self.advancedSearchFilter.items():
            query= query.filter(getattr(AliOrderModel, attr).like("%%%s%%" % value))
        return query
    
    def pageInfoUpdate(self):
        self.offsetOfPage = 0
        self.numOfPage = 10
        self.totalPages = ceil(self.queryFilter().count() / self.numOfPage)
    
    def pageButtonStateUpdate(self):
        if self.totalPages == 0 or self.totalPages == 1:
            self.ui.firstPagePushButton.setDisabled(True)
            self.ui.prevPagePushButton.setDisabled(True)
            self.ui.nextPagePushButton.setDisabled(True)
            self.ui.lastPagePushButton.setDisabled(True)
        elif self.offsetOfPage == 0:
            self.ui.firstPagePushButton.setDisabled(True)
            self.ui.prevPagePushButton.setDisabled(True)
            self.ui.nextPagePushButton.setEnabled(True)
            self.ui.lastPagePushButton.setEnabled(True)
        elif self.offsetOfPage == (self.totalPages - 1):
            self.ui.firstPagePushButton.setEnabled(True)
            self.ui.prevPagePushButton.setEnabled(True)
            self.ui.nextPagePushButton.setDisabled(True)
            self.ui.lastPagePushButton.setDisabled(True)
        else:
            self.ui.firstPagePushButton.setEnabled(True)
            self.ui.prevPagePushButton.setEnabled(True)
            self.ui.nextPagePushButton.setEnabled(True)
            self.ui.lastPagePushButton.setEnabled(True)
    
    def firstPage(self):
        if self.totalPages > 0:
            self.offsetOfPage = 0
            self.setHtml()
    
    def prevPage(self):
        if self.totalPages > 0 and self.offsetOfPage > 0:
            self.offsetOfPage -= 1
            self.setHtml()
    
    def nextPage(self):
        if self.totalPages > 0 and self.offsetOfPage < (self.totalPages - 1):
            self.offsetOfPage += 1
            self.setHtml()
    
    def lastPage(self):
        if self.totalPages > 0:
            self.offsetOfPage = self.totalPages - 1
            self.setHtml()
        
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
        
    def advancedSearchToggled(self, on):
        if not on and len(self.advancedSearchFilter) > 0:
            self.advancedSearchFilter.clear()
            self.pageInfoUpdate()
            self.setHtml()
    
    def advancedSearch(self):
        buyerPhone = self.ui.buyerPhoneLineEdit.text().strip()
        toArea = self.ui.toAreaLineEdit.text().strip()
        toFullName = self.ui.toFullNameLineEdit.text().strip()
        toMobile = self.ui.toMobileLineEdit.text().strip()
        
        self.advancedSearchFilter.clear()
        
        if len(buyerPhone) > 0:
            self.advancedSearchFilter['buyerPhone'] = buyerPhone
        
        if len(toArea) > 0:
            self.advancedSearchFilter['toArea'] = toArea
        
        if len(toFullName) > 0:
            self.advancedSearchFilter['toFullName'] = toFullName
        
        if len(toMobile) > 0:
            self.advancedSearchFilter['toMobile'] = toMobile
        
        self.pageInfoUpdate()
        self.setHtml()
        
    def advancedSearchClear(self):
        self.ui.buyerPhoneLineEdit.setText('')
        self.ui.toAreaLineEdit.setText('')
        self.ui.toFullNameLineEdit.setText('')
        self.ui.toMobileLineEdit.setText('')
        
    def linkClicked(self, url):
        QDesktopServices.openUrl(url)
        
    def setHtml(self):
        self.pageButtonStateUpdate()
        if self.totalPages > 0:
            self.ui.pageNumLabel.setText('{0} / {1}'.format(self.offsetOfPage + 1, self.totalPages))
        else:
            self.ui.pageNumLabel.setText('0 / 0')
        orderList = []
        for model in self.queryFilter().order_by(desc(AliOrderModel.gmtCreate)).offset(self.offsetOfPage * self.numOfPage).limit(self.numOfPage):
            orderList.append(dict(
                buyerPhone = model.buyerPhone,
                carriage = model.carriage,
                gmtCreate = model.gmtCreate,
                orderId = model.orderId,
                status = model.status,
                sumProductPayment = model.sumProductPayment,
                sumPayment = model.sumPayment,
                orderEntries = json.loads(model.orderEntries),
                logisticsOrderList = json.loads(model.logisticsOrderList) if model.logisticsOrderList else None,
                toFullName = model.toFullName,
                toMobile = model.toMobile,
                toArea = model.toArea,
            ))
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('orderlist.html')
        self.ui.webView.setHtml(template.render(orderList = orderList))