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


from PyQt5.QtCore import (Qt, QObject, QCoreApplication, QDate, QDateTime,
                          QTimer, QProcess, QUrl)
from PyQt5.QtCore import QFile, QProcess,QRegExp
from PyQt5.QtWidgets import (QDialog, QMessageBox, QFileDialog, QSpacerItem,
                             QSizePolicy, QPushButton, QDialogButtonBox,
                             QHeaderView, QTableWidgetItem)
from PyQt5.QtGui import QDesktopServices, QRegExpValidator, QBrush, QColor
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

import json
from math import ceil
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import Column, ForeignKey, \
     Integer, Float, String, DateTime, \
     create_engine, desc, or_, func
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.pool import NullPool

from ui_taobaoassistantsettingdialog import Ui_TaobaoAssistantSettingDialog
from ui_taobaoorderlogisticsupdatedialog import Ui_TaobaoOrderLogisticsUpdateDialog
from ui_orderlistreviewdialog import Ui_OrderListReviewDialog
from settings import Settings
from orm import *

AutoMapBase = automap_base()

TaobaoTrade = None
TaobaoTradeEx =None
TaobaoOrder = None
fbdSession = None

class TaobaoAssistantFdb(QObject):
    pInstance = None
    
    @classmethod
    def instance(cls):
        if cls.pInstance is None:
            cls.pInstance = cls()
        return cls.pInstance

    def __init__(self, parent=None):
        super(TaobaoAssistantFdb, self).__init__(parent)
        self.settings = Settings.instance()
        self.settings.taobao_assistant_install_path_changed.connect(self.fdbConnect)
        self.fdbConnect()
    
    def fdbUrl(self):
        tbaUser = self.settings.resource_owner
        tbaPath = self.settings.taobao_assistant_install_path
        return sqlalchemy.engine.url.URL('firebird', username='SYSDBA', password='masterkey',
                                         database = tbaPath + '/users/' + tbaUser + '/APPTRADE.DAT',
                                         query={'charset': 'utf-8'})
    
    def fdbConnect(self):
        self.engine = create_engine(self.fdbUrl(), poolclass=NullPool)
        self.connection = engine.connect()
        AutoMapBase.prepare(self.engine, reflect=True)
        global TaobaoTrade, TaobaoTradeEx, TaobaoOrder, fbdSession
        TaobaoTrade = AutoMapBase.classes.trade
        TaobaoTradeEx = AutoMapBase.classes.tradeex
        TaobaoOrder = AutoMapBase.classes.orders
        fbdSession = sessionmaker(self.engine)()
    
    def fdbDisconnect(self):
        #self.connection.close()
        #self.engine.dispose()
        fbdSession.close()
        

_translate = QCoreApplication.translate

def taobaoAssistantWorkbenchName():
    return 'TaobaoWorkbench.exe'

def taobaoAssistantWorkbench():
    return '{}/{}'.format(Settings.instance().taobao_assistant_install_path,
                          taobaoAssistantWorkbenchName())

def taobaoAssistantWorkbenchIsRunning():
    process = QProcess()
    process.start('tasklist')
    process.waitForFinished()
    tasklist = process.readAllStandardOutput()
    return tasklist.indexOf(taobaoAssistantWorkbenchName()) != -1

def taobaoAssistantInstallPathCheck():
    return QFile.exists(taobaoAssistantWorkbench())

def taobaoAssistantInstallPathVerify(path):
    return QFile.exists('{}/{}'.format(path, taobaoAssistantWorkbenchName()))

def taobaoAssistantWorkbenchLaunch():
    QDesktopServices.openUrl(QUrl.fromLocalFile(taobaoAssistantWorkbench()))

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
            if not taobaoAssistantInstallPathVerify(installPath):
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
        
        TaobaoAssistantFdb.instance()
        
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
            
    def closeEvent(self, event):
        TaobaoAssistantFdb.instance().fdbDisconnect()
        super(TaobaoOrderListReviewDialog, self).closeEvent(event)
        
    def queryFilter(self, count = False):
        if not count:
            query = fbdSession.query(TaobaoTrade)
        else:
            query = fbdSession.query(func.count(TaobaoTrade.tid))
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
        
    def waitSellerSendGoods(self):
        self.fuzzySearch = ''
        self.waitSellerSendGoodsButton.setStyleSheet('color: #f50; font: bold')
        self.waitBuyerPayButton.setStyleSheet('')
        self.allOrdersButton.setStyleSheet('')
        self.statusFilter = 3
        self.pageInfoUpdate()
        self.setHtml()
    
    def waitBuyerPay(self):
        self.fuzzySearch = ''
        self.waitSellerSendGoodsButton.setStyleSheet('')
        self.waitBuyerPayButton.setStyleSheet('color: #f50; font: bold')
        self.allOrdersButton.setStyleSheet('')
        self.statusFilter = 2
        self.pageInfoUpdate()
        self.setHtml()
    
    def allOrders(self):
        self.fuzzySearch = ''
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
            self.ui.pageNumLabel.setText('{} / {} - ({})'.format(self.offsetOfPage + 1, self.totalPages, self.totalCount))
        else:
            self.ui.pageNumLabel.setText('0 / 0 - (0)')
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
            logistics = fbdSession.query(TaobaoTradeEx).filter_by(tid = trade.tid).one()
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
                post_fee = trade.post_fee,
                orders = orders,
                logistics = dict(
                    out_sid = logistics.out_sid,
                    company_code = logistics.company_code,
                    company_name = logistics.company_name,
                ),
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
        
class TaobaoOrderLogisticsUpdateDialog(QDialog):
    def __init__(self, parent=None):
        super(TaobaoOrderLogisticsUpdateDialog, self).__init__(parent)
        self.ui = Ui_TaobaoOrderLogisticsUpdateDialog()
        self.ui.setupUi(self)
        
        self.ui.buttonBox.accepted.connect(self.logisticsUpdateAccept)
        self.ui.buttonBox.rejected.connect(self.logisticsUpdateReject)
        
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setHorizontalHeaderLabels([
            _translate('TaobaoOrderLogisticsUpdateDialog', 'Order ID'),
            _translate('TaobaoOrderLogisticsUpdateDialog', 'Logistics Company'),
            _translate('TaobaoOrderLogisticsUpdateDialog', 'Logistics Number'),
            _translate('TaobaoOrderLogisticsUpdateDialog', 'Pay Time'),
            _translate('TaobaoOrderLogisticsUpdateDialog', 'Send Time'),
        ])
        table = self.ui.tableWidget
        
        TaobaoAssistantFdb.instance()
        
        totalCount = 0
        count = 0
        for tid, pay_time, receiver_name in fbdSession.query(
            TaobaoTrade.tid,
            TaobaoTrade.pay_time,
            TaobaoTrade.receiver_name).filter(TaobaoTrade.status == 3):
            row = totalCount
            table.insertRow(row)
            totalCount += 1
            taobaoTradeEx = fbdSession.query(TaobaoTradeEx).filter_by(tid = tid).one()
            aliOrderModel = session.query(AliOrderModel.gmtCreate, AliOrderModel.logisticsOrderList) \
                .filter(AliOrderModel.toFullName == receiver_name).order_by(desc(AliOrderModel.gmtCreate)).first()
            table.setItem(row, 0, QTableWidgetItem(str(tid)))
            table.setItem(row, 3, QTableWidgetItem(str(pay_time)))
            if taobaoTradeEx.company_code:
                table.setItem(row, 1, QTableWidgetItem(taobaoTradeEx.company_name))
                table.setItem(row, 2, QTableWidgetItem(taobaoTradeEx.out_sid))
                if aliOrderModel and aliOrderModel[1]:
                    logistics = json.loads(aliOrderModel[1])[0]
                    table.setItem(row, 4, QTableWidgetItem(logistics['gmtSend']))
            elif aliOrderModel and aliOrderModel[1]:
                # get first logistic information
                gmtCreate = aliOrderModel[0]
                logistics = json.loads(aliOrderModel[1])[0]
                timedelta = gmtCreate - pay_time
                usedSid = fbdSession.query(TaobaoTradeEx).filter_by(
                    out_sid = logistics['logisticsBillNo']).one_or_none()
                # taobao pay time must be in front of ali order create
                # and the days should not be exceed 5 days
                # and the logistic number must have not been used
                if timedelta.days < 0 or timedelta.days > 5 or usedSid:
                    continue
                taobaoTradeEx.company_code, taobaoTradeEx.company_name, taobaoTradeEx.out_sid = \
                logistics['companyNo'], logistics['companyName'], logistics['logisticsBillNo']
                table.setItem(row, 1, QTableWidgetItem(logistics['companyName']))
                table.setItem(row, 2, QTableWidgetItem(logistics['logisticsBillNo']))
                table.setItem(row, 4, QTableWidgetItem(logistics['gmtSend']))
                table.item(row, 0).setForeground(QBrush(QColor('#f50')))
                table.item(row, 1).setForeground(QBrush(QColor('#f50')))
                table.item(row, 2).setForeground(QBrush(QColor('#f50')))
                table.item(row, 3).setForeground(QBrush(QColor('#f50')))
                table.item(row, 4).setForeground(QBrush(QColor('#f50')))
                count += 1
            else:
                pass
        
        self.ui.qunatityLineEdit.setText('{} / {}'.format(count, totalCount))
        if count == 0:
            self.ui.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)
            self.ui.tbaUpdateLabel.setHidden(True)
        else:
            self.ui.aliUpdateLabel.setHidden(True)
        
    def closeEvent(self, event):
        self.logisticsUpdateReject()
        super(TaobaoOrderLogisticsUpdateDialog, self).closeEvent(event)
        
    def logisticsUpdateAccept(self):
        fbdSession.commit()
        TaobaoAssistantFdb.instance().fdbDisconnect()
        taobaoAssistantWorkbenchLaunch()
    
    def logisticsUpdateReject(self):
        if fbdSession.dirty:
            fbdSession.rollback()
        TaobaoAssistantFdb.instance().fdbDisconnect()
    