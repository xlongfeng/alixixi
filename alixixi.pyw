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


from PyQt5.QtCore import QDataStream, QSettings, QTimer
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QMainWindow,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)

from ui_refreshtokendialog import Ui_RefreshTokenDialog
from ui_alixixi import Ui_Alixixi

from cnalibabaopen import CnAlibabaOpen

class RefreshTokenDialog(QDialog):
    def __init__(self, parent=None):
        super(RefreshTokenDialog, self).__init__(parent)
        self.ui = Ui_RefreshTokenDialog()
        self.ui.setupUi(self)
        
        self.ui.updatePushButton.clicked.connect(self.requestAccessToken)
        
        self.cnAlibabaOpen = CnAlibabaOpen(self)
        self.cnAlibabaOpen.openApiResponse.connect(self.responseAccessToken)
        
    def requestAccessToken(self):
        if len(self.ui.refreshTokenLineEdit.text()) > 0:
            self.cnAlibabaOpen.accessTokenRequest({'refresh_token': self.ui.refreshTokenLineEdit.text()})
    
    def requestRefreshToken(self):
        self.cnAlibabaOpen.refreshTokenRequest({'refresh_token': '74831383-be8c-473e-898b-e6a90cd1f7e6', 'access_token': '13d99a84-195c-4b51-8032-107c526d4d82'})
    
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

class Alixixi(QMainWindow):
    def __init__(self, parent=None):
        super(Alixixi, self).__init__(parent)
        self.ui = Ui_Alixixi()
        self.ui.setupUi(self)
        
        self.refreshTokenDialg = RefreshTokenDialog(self)
        
        self.cnAlibabaOpen = CnAlibabaOpen(self)
        self.cnAlibabaOpen.openApiResponse.connect(self.responseNewFortune)
        
        self.ui.refreshTokenPushButton.clicked.connect(self.refreshTokenDialg.exec)

    def requestNewFortune(self):
        self.cnAlibabaOpen.openApiRequest('member.get', {'memberId': 'b2b-256074649203e5d'})

    def responseNewFortune(self, response):
        print(response)

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    alixixi = Alixixi()
    alixixi.show()
    sys.exit(app.exec_())
