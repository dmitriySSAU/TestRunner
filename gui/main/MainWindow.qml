import QtQuick 2.12
import QtQuick.Window 2.12
import QtQuick.Layouts 1.3
import QtQuick.Controls 2.12
import "output.js" as OutputJS
import PyMainWindow 1.0

Window {
    id: mainWindow
    visible: true
    width: 640
    height: 480
    title: qsTr("Инструмент автотестирования Runner")

    signal redirectMessage(string message)

    ColumnLayout {
        id: test
        x: 0
        y: 0

        MainWindow {
            id: pyclass
        }

        TopBarMenu {
            id: mainMenu
        }

        Text {
            text: "Тест кейсы"
            Layout.leftMargin: 10
            leftPadding: 10
            style: Text.Normal
            font.bold: true
            font.pointSize: 12
            font.family: "Times New Roman"
            renderType: Text.QtRendering
        }

        RowLayout {
            width: 640
            spacing: 12.5
            Layout.fillHeight: false
            Layout.fillWidth: true

            ComboBox{
                id: testCaseComboBox
                width: 200
                height: 35
                Layout.preferredWidth:  width
                Layout.preferredHeight: height
                displayText: "Выберите тест кейс"
                Layout.leftMargin: 10
                currentIndex: 0
                font.pointSize: 10
                font.family: "Times New Roman"
                model: pyclass.test_cases
            }
        }

        OutputComponent {
            id: outputComponent
        }


    }
    Connections {
            target: pyclass
            onGotMessage: {
                console.log(message)
                redirectMessage(OutputJS.print_error(message))
            }
        }
}
