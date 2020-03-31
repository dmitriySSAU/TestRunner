import QtQuick 2.0
import QtQuick.Layouts 1.3

Rectangle {
    id: mainMenu
    width: mainWindow.width
    height: 55
    Rectangle {
        height: 3
        transformOrigin: Item.Center
        gradient: Gradient {
            GradientStop {
                position: 0.034
                color: "#161618"
            }

            GradientStop {
                position: 0.633
                color: "#886a6a"
            }
        }
        anchors.top: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
    }
    RowLayout {
        Image {
            sourceSize.height: 50
            sourceSize.width: 50
            source: "images/analizator.png"
        }
        Image {
            sourceSize.height: 50
            sourceSize.width: 50
            source: "images/edit_test_case.png"
        }
        Image {
            sourceSize.height: 50
            sourceSize.width: 50
            source: "images/settings.png"
        }
        Image {
            sourceSize.height: 50
            sourceSize.width: 50
            source: "images/help.png"
        }
    }
}

