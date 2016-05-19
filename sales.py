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


from PyQt5.QtCore import Qt, QCoreApplication, QDate, QTimer, QUrl, QFile
from PyQt5.QtWidgets import (QApplication, QWidget, QComboBox, QDialog,
                             QMessageBox)
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage

from math import ceil
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, or_, func

from ui_salesreportingdialog import Ui_SalesReportingDialog
from orm import *

_translate = QCoreApplication.translate

class SalesReportingDialog(QDialog):
    def __init__(self, parent=None):
        super(SalesReportingDialog, self).__init__(parent)
        self.ui = Ui_SalesReportingDialog()
        self.ui.setupUi(self)
        self.resize(1050, 640)
        
        self.ui.prevPushButton.clicked.connect(self.prevView)
        self.ui.nextPushButton.clicked.connect(self.nextView)
        
        #self.ui.webView.settings().setAttribute(QWebSettings.OfflineStorageDatabaseEnabled, True)
        #self.ui.webView.settings().setAttribute(QWebSettings.OfflineWebApplicationCacheEnabled, True)
        #self.ui.webView.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        #self.ui.webView.settings().enablePersistentStorage()
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.ui.webView.linkClicked.connect(self.linkClicked)
        
        QTimer.singleShot(100, self.setHtml)
        
    def prevView(self):
        pass
    
    def nextView(self):
        pass
    
    def linkClicked(self, url):
        QDesktopServices.openUrl(url)
        
    def setHtml(self):
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('chart.html')
        self.ui.webView.setHtml(template.render(), QUrl('qrc:///'))