import QtQuick 2.0
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.3

Item {
    width: 245
    height: 180
    TextArea {
        id: outputTextArea
        width: parent.width
        height: parent.height
        readOnly: false
        textFormat: TextEdit.RichText
    }
    Connections {
        target: mainWindow
        onRedirectMessage: {
            outputTextArea.append(message)
        }
    }
}
