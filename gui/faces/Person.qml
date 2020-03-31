import QtQuick 2.4
import "test.js" as MyScripts

Component {
    id: delegateFace

    Item {
        id: faceItem
        state: ""
        property string name_person: "Dima"
        width: {
            var w = mainWindow.width / 2
            return w
        }
        height: MyScripts.minimum(mainWindow.height, 200)
        Row {
            Text {id: faceText; text: name }
            Image {
                id: faceImage
                width: 100
                height: 100
                source: img
                smooth: true
            }

        }
        states: [
            State {
                name: "State1"
                PropertyChanges {
                    target: faceItem
                    name_person: "Dima"
                }
            },
            State {
                name: "State2"
                PropertyChanges {
                    target: faceItem
                    name_person: "Dimoooon"
                }
            }
        ]
        transitions: [
            Transition {
                from: "State1"
                to: "State2"
                PropertyAnimation {
                    target: faceImage
                    properties: "x"
                    easing.type: Easing.InExpo
                    duration: 2000
                }
            }
        ]
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            onEntered: faceItem.state = "State2"
            onExited: faceItem.state = "State1"
        }
    }

}
