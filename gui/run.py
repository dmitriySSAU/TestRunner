from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtCore import pyqtProperty, QObject, QSize, pyqtSignal
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlListProperty

import threading
import time


class MainWindow(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._test_cases = ["Тест-кейс 1", "Тест-кейс 2"]
        test = Test(self)
        test.start()

    gotMessage = pyqtSignal(str, arguments=["message"], name="gotMessage")

    @pyqtProperty('QStringList')
    def test_cases(self):
        return self._test_cases

    def emit_test(self):
        self.gotMessage.emit("ERROR!!!")


class Test(threading.Thread):
    def __init__(self, window):
        super().__init__()
        self.window = window

    def run(self) -> None:
        for i in range(50):
            time.sleep(1)
            self.window.emit_test()


def run():
    app = QGuiApplication([])

    engine = QQmlApplicationEngine()
    qmlRegisterType(MainWindow, 'PyMainWindow', 1, 0, 'MainWindow')
    engine.load(QUrl.fromLocalFile("./gui/main/MainWindow.qml"))
    app.exec_()