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
                             QPushButton, QDialogButtonBox)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import json
from math import ceil
from datetime import datetime
from enum import Enum
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, or_, func

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
    Mode = Enum('Mode', 'auto custom defined')
    
    def __init__(self, createStartTime, createEndTime, mode=Mode.defined, parent=None):
        super(OrderListGetDialog, self).__init__(parent)
        self.ui = Ui_OrderListGetDialog()
        self.ui.setupUi(self)
        self.ui.createStartTimeDateEdit.setDate(createStartTime)
        self.ui.createEndTimeDateEdit.setDate(createEndTime)
        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        self.ui.buttonBox.rejected.connect(self.orderListGetRequestAbort)
        
        self.mode = mode
        
        self.settings = Settings(self)
        self.cnAlibabaOpen = CnAlibabaOpen.instance()
        self.cnAlibabaOpen.openApiResponse.connect(self.orderListGetReponse)
        self.cnAlibabaOpen.openApiResponse.connect(self.orderDetailGetResponse)
        
        if self.mode != self.Mode.custom:
            self.ui.createStartTimeDateEdit.setReadOnly(True)
            self.ui.createEndTimeDateEdit.setReadOnly(True)
            if self.validateDateRange():
                QTimer.singleShot(100, self.prepareOrderListGet)
        else:
            self.ui.buttonBox.setStandardButtons(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
            self.ui.buttonBox.clicked.connect(self.applyOrderListGet)
    
    def closeEvent(self, event):
        self.orderListGetRequestAbort()
        super(OrderListGetDialog, self).closeEvent(event)
    
    def prepareOrderListGet(self):
        self.orderList = dict()
        self.orderDetailIdList = []
        self.createStartTime = self.ui.createStartTimeDateEdit.date().toString('yyyyMMdd00000000+0800')
        self.createEndTime = self.ui.createEndTimeDateEdit.date().toString('yyyyMMdd23595900+0800')
        self.totalCount = 0
        self.count = 0
        self.page = 1
        self.orderModelId = ''
        self.taskDone = False
        self.ui.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)
        self.orderListGetRequest()
    
    def applyOrderListGet(self, button):
        if self.ui.buttonBox.standardButton(button) == QDialogButtonBox.Apply:
            if self.validateDateRange():
                self.prepareOrderListGet()
            
    def validateDateRange(self):
        createStartTime = self.ui.createStartTimeDateEdit.date()
        createEndTime = self.ui.createEndTimeDateEdit.date()
        if createStartTime > createEndTime:
            QMessageBox.warning(self, _translate('OrderListGetDialog', 'Ali Order Query'),
                                _translate('OrderListGetDialog', 'Date range error, start time later than the end of time'))
            return False
        if createStartTime.addMonths(1) < createEndTime:
            QMessageBox.warning(self, _translate('OrderListGetDialog', 'Ali Order Query'),
                                _translate('OrderListGetDialog', 'Date range error, time range is too long, must be less than 1 month'))
            return False
        return True
    
    def orderListGetRequestAbort(self):
        if session.dirty:
            session.rollback()
        
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
            self.taskDone = True
            if self.mode == self.Mode.auto:
                self.settings.ali_order_last_update_time = datetime.today()
                self.accept()
            else:
                self.ui.buttonBox.setStandardButtons(QDialogButtonBox.Open | QDialogButtonBox.Close)
        
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
                if 'specInfoModel' in orderEntryModel:
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
                QMessageBox.information(self, _translate('OrderListGetDialog', 'Ali Order List'),
                                        _translate('OrderListGetDialog', 'Empty order list'))
                self.reject()
                return
            else:
                self.ui.quantityLineEdit.setText(str(self.totalCount))
                self.ui.progressBar.setRange(0, self.totalCount)
        self.orderListAppend(orderListResult['modelList'])
                
    def orderDetailGetResponse(self, response):
        if 'orderModel' not in response:
            return
        orderModel = response['orderModel']
        orderId = orderModel['id']
        model = session.query(AliOrderModel).filter_by(orderId = orderId).one()
        model.toArea = orderModel['toArea']
        model.toFullName = orderModel['toFullName']
        if 'toMobile' in orderModel:
            model.toMobile = orderModel['toMobile']
        if 'toPhone' in orderModel:
            model.toPhone = orderModel['toPhone']
        if 'logisticsOrderList' in orderModel:
            logisticsOrderList = []
            for logisticsOrderModel in orderModel['logisticsOrderList']:
                logisticsOrderList.append({
                    'logisticsOrderNo': logisticsOrderModel['logisticsOrderNo'],
                    'companyName': logisticsOrderModel['logisticsCompany']['companyName'],
                    'companyNo': logisticsOrderModel['logisticsCompany']['companyNo'],
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
        self.resize(1050, 640)
        
        self.ui.firstPagePushButton.clicked.connect(self.firstPage)
        self.ui.prevPagePushButton.clicked.connect(self.prevPage)
        self.ui.nextPagePushButton.clicked.connect(self.nextPage)
        self.ui.lastPagePushButton.clicked.connect(self.lastPage)
        
        self.ui.searchPushButton.clicked.connect(self.advancedSearch)
        self.ui.clearPushButton.clicked.connect(self.advancedSearchClear)
        
        self.fuzzySearch = ''
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
            
    def queryFilter(self, count = False):
        if not count:
            query = session.query(AliOrderModel)
        else:
            query = session.query(func.count(AliOrderModel.id))
        value = self.fuzzySearch
        if len(value) > 0:
            query= query.filter(or_(AliOrderModel.logisticsOrderList.like('%%"logisticsBillNo": "%s"%%' % value),
                                    AliOrderModel.toArea.like('%%%s%%' % value),
                                    AliOrderModel.toFullName.like('%%%s%%' % value),
                                    AliOrderModel.toMobile.like('%%%s%%' % value),
                                    AliOrderModel.toPhone.like('%%%s%%' % value)))
        return query
    
    def pageInfoUpdate(self):
        self.offsetOfPage = 0
        self.numOfPage = 10
        self.totalCount = self.queryFilter(True).scalar()
        self.totalPages = ceil(self.totalCount / self.numOfPage)
    
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
    
    def advancedSearch(self):
        self.fuzzySearch = self.ui.searchLineEdit.text().strip()
        self.pageInfoUpdate()
        self.setHtml()
        
    def advancedSearchClear(self):
        self.ui.searchLineEdit.setText('')
        
    def linkClicked(self, url):
        QDesktopServices.openUrl(url)
        
    def setHtml(self):
        self.pageButtonStateUpdate()
        if self.totalPages > 0:
            self.ui.pageNumLabel.setText('{} / {} - ({})'.format(self.offsetOfPage + 1, self.totalPages, self.totalCount))
        else:
            self.ui.pageNumLabel.setText('0 / 0 - (0)')
        orderList = []
        for model in self.queryFilter().order_by(desc(AliOrderModel.gmtCreate)).offset(self.offsetOfPage * self.numOfPage).limit(self.numOfPage):
            orderList.append(dict(
                carriage = model.carriage,
                gmtCreate = model.gmtCreate,
                orderId = model.orderId,
                status = model.status,
                sumProductPayment = model.sumProductPayment,
                sumPayment = model.sumPayment,
                orderEntries = json.loads(model.orderEntries),
                logisticsOrderList = json.loads(model.logisticsOrderList) if model.logisticsOrderList else None,
                toArea = model.toArea,
                toFullName = model.toFullName,
                toPhone = model.toPhone,
                toMobile = model.toMobile,
            ))
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('orderlist.html')
        self.ui.webView.setHtml(template.render(orderList = orderList))