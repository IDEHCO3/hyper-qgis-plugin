
# coding: utf-8

########################################
# requests.py
# Este script contém classes para conexão com uma url na internet
# Para usá-la basta chamar o método request_method(url, method)
# ou uma de suas implementações get(), post(), options() ou head().
# Esta classe a classe QNetworkAccessManger do Qt para fazer requisições
########################################

""" TODO: passagem de parâmetros com **data para a request
"""

from PyQt4.QtCore import QObject, QUrl, QEventLoop, pyqtSignal
from PyQt4.QtNetwork import QNetworkRequest, QNetworkAccessManager

# Esta class serve como proxy entre QNetworkReply e o sistema.
# Nela há um tratamento melhorado do output de QNetworkReply
class Reply(QObject):
    requestStarted = pyqtSignal()
    readyRead = pyqtSignal()
    downloadProgress = pyqtSignal(unicode, unicode)
    finished = pyqtSignal()
    error = pyqtSignal(unicode)

    def __init__(self, command, url=""):
        super(Reply, self).__init__()
        self.command = command
        self.url = url

        self._reply = None

    def __getattr__(self, item):
        return getattr(self._reply, item)

    @property
    def reply(self):
        return self._reply

    @reply.setter
    def reply(self, reply):
        self._reply = reply

        self._reply.readyRead.connect(self.readyRead)
        self._reply.finished.connect(self.finished)
        self._reply.downloadProgress.connect(self._download_progress)
        self._reply.error.connect(self._error_happened)

    @reply.deleter
    def reply(self):
        self._reply.readyRead.disconnect()
        self._reply.finished.disconnect()
        self._reply.downloadProgress.disconnect()
        self._reply.error.disconnect()

        self._reply = None

    def _error_happened(self):
        self.error.emit(self._reply.errorString())

    def _download_progress(self, received, total):
        self.downloadProgress.emit(self._sizeof_fmt(received), self._sizeof_fmt(total))

    def _sizeof_fmt(self, num):
        for unit in ['', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
            if abs(num) < 1024.0:
                return "%3.1f%s" % (num, unit)

            num /= 1024.0

        return "%.1f%s" % (num, 'Yi')

    def response(self):
        self.reply = self.command()
        self.requestStarted.emit()

        loop = QEventLoop()
        self.reply.finished.connect(loop.exit)

        loop.exec_()

        if self.reply.isFinished():
            qbytearray = self.reply.readAll()

            # Transform header from reply into key value pairs
            header_data = {}
            for tup in self.reply.rawHeaderPairs():
                header_data.update({tup[0].data().lower(): tup[1].data()})

            self.reply.deleteLater()

            status_code = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            status_phrase = self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute)

            return {
                'url': self.url,
                'status_code': status_code,
                'status_phrase': status_phrase,
                'headers': header_data,
                'body': qbytearray.data()
            }

        return {}


class QgsRequest:
    def __init__(self, url, method='GET', **data):
        self.manager = QNetworkAccessManager()
        self.method = method
        self.url = QUrl(url)
        self.request = QNetworkRequest(self.url)

    def send(self):
        # Switch to get the appropriate function to process the request
        switch = {
            'get': self.manager.get,
            'options': lambda request: self.manager.sendCustomRequest(request, 'OPTIONS'),
            'head': self.manager.head,
            'put': self.manager.put
        }

        access_method = switch.get(self.method.lower())

        reply_command = lambda: access_method(self.request)
        reply = Reply(reply_command, self.url)

        return reply


def request_method(url, method):
    request = QgsRequest(url, method)

    return request.send()


def get(url, **data):
    return request_method(url, 'GET')


def post(url, **data):
    return request_method(url, 'POST')


def options(url, **data):
    return request_method(url, 'OPTIONS')


def head(url, **data):
    return request_method(url, 'HEAD')
