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
from PyQt5.QtCore import QFile, QProcess,QRegExp
from PyQt5.QtWidgets import (QDialog, QMessageBox, QFileDialog, QSpacerItem,
                             QSizePolicy, QPushButton)
from PyQt5.QtGui import QDesktopServices, QRegExpValidator
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import json
from math import ceil
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, or_

from ui_taobaoassistantsettingdialog import Ui_TaobaoAssistantSettingDialog
from ui_orderlistreviewdialog import Ui_OrderListReviewDialog
from settings import Settings
from orm import *

_translate = QCoreApplication.translate

def taobaoAssistantWorkbenchName():
    return 'Workbench.exe'

def taobaoAssistantWorkbenchPath(path):
    return '{}/{}'.format(path, taobaoAssistantWorkbenchName())

def taobaoAssistantWorkbenchIsRunning():
    process = QProcess()
    process.start('tasklist')
    process.waitForFinished()
    tasklist = process.readAllStandardOutput().data().decode('utf-8')
    return tasklist.find(taobaoAssistantWorkbenchName()) != -1

def taobaoAssistantInstallPathCheck(path):
    return QFile.exists(taobaoAssistantWorkbenchPath(path))

class TaobaoAssistantSettingDialog(QDialog):
    def __init__(self, parent=None):
        super(TaobaoAssistantSettingDialog, self).__init__(parent)
        self.ui = Ui_TaobaoAssistantSettingDialog()
        self.ui.setupUi(self)
        self.settings = Settings(self)
        self.ui.installPathLineEdit.setText(self.settings.taobao_assistant_install_path)
        
        self.ui.browsePushButton.clicked.connect(self.browseInstallPath)
        
    def browseInstallPath(self):
        installPath = QFileDialog.getExistingDirectory(self,
                                         _translate('TaobaoAssistantSettingDialog', 'Taobao assistant install path'),
                                         'C:/')
        if len(installPath) > 0:
            if not taobaoAssistantInstallPathCheck(installPath):
                QMessageBox.warning(self, _translate('TaobaoAssistantSettingDialog', 'Taobao assistant install path'),
                                    _translate('TaobaoAssistantSettingDialog', 'The selected path is not correct'))
            else:
                self.ui.installPathLineEdit.setText(installPath)
            
    def save(self):
        self.settings.taobao_assistant_install_path = self.ui.installPathLineEdit.text()
        
        
class TaobaoOrderListReviewDialog(QDialog):
    def __init__(self, parent=None):
        super(TaobaoOrderListReviewDialog, self).__init__(parent)
        self.ui = Ui_OrderListReviewDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(_translate("TaobaoOrderListReviewDialog", "Taobao Order List"))
        self.resize(1050, 640)
        
        self.ui.searchLineEdit.setValidator(QRegExpValidator(QRegExp('[a-zA-Z0-9\.\-\ ]+'), self))
        
        self.ui.firstPagePushButton.clicked.connect(self.firstPage)
        self.ui.prevPagePushButton.clicked.connect(self.prevPage)
        self.ui.nextPagePushButton.clicked.connect(self.nextPage)
        self.ui.lastPagePushButton.clicked.connect(self.lastPage)
        
        self.ui.searchPushButton.clicked.connect(self.advancedSearch)
        self.ui.clearPushButton.clicked.connect(self.advancedSearchClear)
        
        self.statusFilter = 3
        self.fuzzySearch = ''
        self.pageInfoUpdate()
        
        self.ui.webView.settings().setAttribute(QWebSettings.OfflineStorageDatabaseEnabled, True)
        self.ui.webView.settings().setAttribute(QWebSettings.OfflineWebApplicationCacheEnabled, True)
        self.ui.webView.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        self.ui.webView.settings().enablePersistentStorage()
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.linkClicked.connect(self.linkClicked)
        
        self.waitSellerSendGoodsButton = QPushButton(_translate('OrderListReview', 'Wait Seller Send Goods'))
        self.waitSellerSendGoodsButton.clicked.connect(self.waitSellerSendGoods)
        self.ui.customFilterHorizontalLayout.addWidget(self.waitSellerSendGoodsButton)
        self.waitBuyerPayButton = QPushButton(_translate('OrderListReview', 'Wait Buyer Pay'))
        self.waitBuyerPayButton.clicked.connect(self.waitBuyerPay)
        self.ui.customFilterHorizontalLayout.addWidget(self.waitBuyerPayButton)
        self.allOrdersButton = QPushButton(_translate('OrderListReview', 'All Orders'))
        self.allOrdersButton.clicked.connect(self.allOrders)
        self.ui.customFilterHorizontalLayout.addWidget(self.allOrdersButton)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.ui.customFilterHorizontalLayout.addItem(spacerItem)
        
        if self.totalPages == 0:
            self.setHtml()
        else:
            self.ui.webView.setHtml(_translate('OrderListReview', 'Loading, wait a monent ...'))
            QTimer.singleShot(100, self.waitSellerSendGoods)
        
    def queryFilter(self):
        query = fbdSession.query(TaobaoTrade)
        if self.statusFilter != -1:
            query = query.filter(TaobaoTrade.status == self.statusFilter)
        value = self.fuzzySearch
        if len(value) > 0:
            query= query.filter(or_(TaobaoTrade.tid.like('%%%s%%' % value),
                                    TaobaoTrade.alipay_no.like('%%%s%%' % value),
                                    TaobaoTrade.buyer_nick.like('%%%s%%' % value),
                                    TaobaoTrade.buyer_alipay_no.like('%%%s%%' % value),
                                    TaobaoTrade.receiver_name.like('%%%s%%' % value),
                                    TaobaoTrade.receiver_mobile.like('%%%s%%' % value),
                                    TaobaoTrade.receiver_phone.like('%%%s%%' % value)))
            
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
    
    def advancedSearch(self):
        self.fuzzySearch = self.ui.searchLineEdit.text().strip()
        self.pageInfoUpdate()
        self.setHtml()
        
    def advancedSearchClear(self):
        self.ui.searchLineEdit.setText('')
        
    def waitSellerSendGoods(self):
        self.waitSellerSendGoodsButton.setStyleSheet('color: #f50; font: bold')
        self.waitBuyerPayButton.setStyleSheet('')
        self.allOrdersButton.setStyleSheet('')
        self.statusFilter = 3
        self.pageInfoUpdate()
        self.setHtml()
    
    def waitBuyerPay(self):
        self.waitSellerSendGoodsButton.setStyleSheet('')
        self.waitBuyerPayButton.setStyleSheet('color: #f50; font: bold')
        self.allOrdersButton.setStyleSheet('')
        self.statusFilter = 2
        self.pageInfoUpdate()
        self.setHtml()
    
    def allOrders(self):
        self.waitSellerSendGoodsButton.setStyleSheet('')
        self.waitBuyerPayButton.setStyleSheet('')
        self.allOrdersButton.setStyleSheet('color: #f50; font: bold')
        self.statusFilter = -1
        self.pageInfoUpdate()
        self.setHtml()
        
    def linkClicked(self, url):
        QDesktopServices.openUrl(url)
        
    def orderStatus(self, status):
        translate = {
            0: _translate('TaobaoOrderListReview', '0'),
            1: _translate('TaobaoOrderListReview', '1'),
            2: _translate('TaobaoOrderListReview', 'WAIT_BUYER_PAY'),
            3: _translate('TaobaoOrderListReview', 'WAIT_SELLER_SEND_GOODS'),
            4: _translate('TaobaoOrderListReview', 'WAIT_BUYER_CONFIRM_GOODS'),
            5: _translate('TaobaoOrderListReview', '5'),
            6: _translate('TaobaoOrderListReview', 'WAIT_BUYER_RATE_GOODS'),
            7: _translate('TaobaoOrderListReview', 'TRADE_FINISHED'),
            8: _translate('TaobaoOrderListReview', 'UNKNOWN_STATUS'),
        }
        return translate[status]
        
    def setHtml(self):
        self.pageButtonStateUpdate()
        if self.totalPages > 0:
            self.ui.pageNumLabel.setText('{0} / {1}'.format(self.offsetOfPage + 1, self.totalPages))
        else:
            self.ui.pageNumLabel.setText('0 / 0')
        tradeList = []
        for trade in self.queryFilter().order_by(desc(TaobaoTrade.created)).offset(self.offsetOfPage * self.numOfPage).limit(self.numOfPage):
            orders = []
            for order in fbdSession.query(TaobaoOrder).filter_by(tid = trade.tid):
                orders.append(dict(
                    oid = order.oid,
                    propertites = order.sku_properties_name.split(';') if order.sku_properties_name else [],
                    num = order.num,
                    title = order.title,
                    price = order.price,
                    refund_status = order.refund_status,
                    total_fee = order.total_fee,
                    payment = order.payment,
                    discount_fee = order.discount_fee,
                    status = self.orderStatus(order.status),
                ))
            logisticsOrderList = []
            for logistics in fbdSession.query(TaobaoTradeEx).filter_by(tid = trade.tid):
                logisticsOrderList.append(dict(
                    out_sid = logistics.out_sid,
                    company_code = logistics.company_code,
                    company_name = logistics.company_name,
                ))
            tradeList.append(dict(
                tid = trade.tid,
                alipay_no = trade.alipay_no,
                created = trade.created,
                pay_time = trade.pay_time,
                payment = trade.payment,
                buyer_nick = trade.buyer_nick,
                buyer_alipay_no = trade.buyer_alipay_no,
                buyer_email = trade.buyer_email,
                buyer_message = trade.buyer_message,
                status = trade.status,
                orders = orders,
                logisticsOrderList = logisticsOrderList,
                receiver_name = trade.receiver_name,
                receiver_phone = trade.receiver_phone,
                receiver_mobile = trade.receiver_mobile,
                receiver_state = trade.receiver_state,
                receiver_city = trade.receiver_city,
                receiver_district = trade.receiver_district,
                receiver_address = trade.receiver_address,
                receiver_zip = trade.receiver_zip,
            ))
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('taobaoorderlist.html')
        self.ui.webView.setHtml(template.render(tradeList = tradeList))