from PyQt5.QtQuick import QQuickImageProvider, QQuickView
from PyQt5.QtGui import QImage, QGuiApplication
from PyQt5.QtCore import QByteArray, QUrl
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from gui.faces import model


class ImageFaceProvider(QQuickImageProvider):
    """Класс для транслирования фото с лицом в формате base64 в окно QML.

    """
    def __init__(self):
        super(ImageFaceProvider, self).__init__(QQuickImageProvider.Image)
        self._images = []

    def requestImage(self, image_id: int, size: int):
        """Переопределнный метод QQuickImageProvider для получения картинки.

        Осуществляется поиск id в хранилище и дальнейше преобразование картинки в байты для загрузки в окно QML.
        :param image_id: индекс картинки в списке
        :param size: размер
        :return:
        """
        for image in self._images:
            if image["id"] == image_id:
                image_base64_bytes = QByteArray(image["image"].encode('utf-8'))
                data = QByteArray.fromBase64(image_base64_bytes)
                q_image = QImage()
                q_image.loadFromData(data)
                return q_image, size

    def append_image(self, img_base64: str) -> int:
        """Метод добавления в хранилище провайдера картинки в формате base64.

        :param img_base64: строка в формате base64
        :return: уникальный id для доступа к этой картинке
        """
        image_id: int = 1
        while True:
            is_image_id_free: bool = True
            for image in self._images:
                if image['id'] == image_id:
                    is_image_id_free = False
                    break
            if is_image_id_free:
                self._images.append({"id": image_id, "image": img_base64})
                return image_id

            image_id += 1

    def remove_image(self, image_id: int) -> bool:
        """Метод удаления картинки из хранилища.

        :param image_id: уникальный id картинки
        :return: либо True, если удаление успешно, либо False, если такой id не был найдет.
        """
        for index, image in self._images:
            if image["id"] == image_id:
                self._images.pop(index)
                return True
        return False


def run():
    app = QGuiApplication([])

    engine = QQmlApplicationEngine()
    qmlRegisterType(model.PersonModel, 'TestModel', 1, 0, 'PersonModel')
    provider = ImageFaceProvider()
    engine.addImageProvider("facesProvider", provider)
    engine.load(QUrl.fromLocalFile("./gui/main/MainWindow.qml"))
    app.exec_()

