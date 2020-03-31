import QtQuick 2.13
import QtQuick.Window 2.13
import QtQuick.Controls 2.0
import TestModel 1.0

Window {
    id: mainWindow
    property bool cond: true
    signal mousePositionChanged(real x, real y)

    visible: true
    width: 640
    height: 480
    title: qsTr("Hello World")
    color: "black"

    onCondChanged: {
        console.log(mainWindow.cond)
    }

    PersonModel
    {
        id: personModel
    }

    ListView {
        anchors {
            fill: parent
        }

        model: personModel.persons
        delegate: Person {}
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: false
        onPressed: {
            if (mouse.button === Qt.LeftButton) {
                        mainWindow.color = "white"
            } else {
                    mainWindow.color = "black"
                }
        }
        onMouseXChanged: mainWindow.mousePositionChanged(mouseX, mouseY)
    }

    onMousePositionChanged: {
        console.log(x + "-" + y)
    }



}
