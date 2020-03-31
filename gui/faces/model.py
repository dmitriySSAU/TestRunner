import threading
import time

from PyQt5.QtCore import pyqtProperty, QObject, QSize, pyqtSignal
from PyQt5.QtQml import qmlRegisterType, QQmlComponent, QQmlEngine, QQmlListProperty


class Person(QObject):
    def __init__(self, _name, _img, parent=None):
        super().__init__(parent)

        self._name = _name
        self._img = _img

    @pyqtProperty('QString')
    def name(self):
        return self._name

    # Define the setter of the 'name' property.
    @name.setter
    def name(self, name):
        self._name = name

    @pyqtProperty('QString')
    def img(self):
        return self._img

    # Define the setter of the 'shoeSize' property.
    @img.setter
    def img(self, img):
        self._img = img


class PersonModel(QObject):
    facesChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # The list which will be accessible from QML.
        self._persons = []
        thread = TestPersonModel(self)
        thread.start()

    @pyqtProperty(QQmlListProperty, notify=facesChanged)
    def persons(self):
        return QQmlListProperty(Person, self, self._persons)

    def addPerson(self, person):
        self._persons.append(person)
        self.facesChanged.emit()


class TestPersonModel(threading.Thread):

    def __init__(self, personModel):
        threading.Thread.__init__(self)
        self.personModel = personModel

    def run(self):
        time.sleep(5)
        for i in range(2):
            person = Person("Dimon", "image://facesProvider/" + str(i))
            self.personModel.addPerson(person)