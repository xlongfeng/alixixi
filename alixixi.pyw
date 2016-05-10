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


from PyQt5.QtGui import QIntValidator, QDesktopServices
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QMainWindow,
                             QGridLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton)

from ui_authorizedialog import Ui_AuthorizeDialog
from ui_alixixi import Ui_Alixixi
from settings import Settings
from cnalibabaopen import CnAlibabaOpen

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
        
class Alixixi(QMainWindow):
    def __init__(self, parent=None):
        super(Alixixi, self).__init__(parent)
        self.ui = Ui_Alixixi()
        self.ui.setupUi(self)
        
        self.ui.authorizePushButton.clicked.connect(self.authorizeRequest)
        
        settings.resource_owner_changed.connect(self.ui.loginIdLineEdit.setText)
        self.ui.loginIdLineEdit.setText(settings.resource_owner)
        
        self.ui.getMemberPushButton.clicked.connect(self.getMemberRequest)
        
    def authorizeRequest(self):
        QDesktopServices.openUrl(cnAlibabaOpen.openApiAuthorizeRequest())
        dialog = AuthorizeDialog(self)
        dialog.exec()

    def getMemberRequest(self):
        cnAlibabaOpen.openApiResponse.connect(self.getMemberResponse)
        cnAlibabaOpen.openApiRequest('member.get', {'memberId': 'b2b-256074649203e5d'})

    def getMemberResponse(self, response):
        print(response)

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    settings = Settings(app)
    cnAlibabaOpen = CnAlibabaOpen(app)
    alixixi = Alixixi()
    alixixi.show()
    sys.exit(app.exec_())
