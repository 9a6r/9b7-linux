
import QtQuick 2.11
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.4

RowLayout {

    spacing: root.font.pointSize

    readonly property var suspend: ["Suspend", config.TranslateSuspend || textConstants.suspend, sddm.canSuspend]
    readonly property var hibernate: ["Hibernate", config.TranslateHibernate || textConstants.hibernate, sddm.canHibernate]
    readonly property var reboot: ["Reboot", config.TranslateReboot || textConstants.reboot, sddm.canReboot]
    readonly property var shutdown: ["Shutdown", config.TranslateShutdown || textConstants.shutdown, sddm.canPowerOff]

    property Item exposedSession

    Repeater {

        id: systemButtons
        model: [suspend, hibernate, reboot, shutdown]

        RoundButton {
            id: powerButton
            text: modelData[1]
            font.pointSize: root.font.pointSize * 0.8
            Layout.alignment: Qt.AlignHCenter
            icon.source: modelData ? Qt.resolvedUrl("../Assets/" + modelData[0] + ".svg") : ""
            icon.height: 2 * Math.round((root.font.pointSize * 3) / 2)
            icon.width: 2 * Math.round((root.font.pointSize * 3) / 2)
            display: AbstractButton.TextUnderIcon
            visible: config.ForceHideSystemButtons != "true" && modelData[2]
            hoverEnabled: true
            palette.buttonText: root.palette.text
            background: Rectangle {
                height: 2
                color: "transparent"
                width: parent.width
                border.width: parent.activeFocus ? 1 : 0
                border.color: "transparent"
                anchors.top: parent.bottom
            }
            Keys.onReturnPressed: clicked()
            onClicked: {
                parent.forceActiveFocus()
                index == 0 ? sddm.suspend() : index == 1 ? sddm.hibernate() : index == 2 ? sddm.reboot() : sddm.powerOff()
            }
            KeyNavigation.up: exposedSession
            KeyNavigation.left: index > 0 ? systemButtons.itemAt(index - 1) : null

            states: [
                State {
                    name: "pressed"
                    when: powerButton.down
                    PropertyChanges {
                        target: powerButton
                        palette.buttonText: Qt.darker(root.palette.highlight, 1.1)
                    }
                    PropertyChanges {
                        target: powerButton.background
                        border.color: Qt.darker(root.palette.highlight, 1.1)
                    }
                },
                State {
                    name: "hovered"
                    when: powerButton.hovered
                    PropertyChanges {
                        target: powerButton
                        palette.buttonText: Qt.lighter(root.palette.highlight, 1.1)
                    }
                    PropertyChanges {
                        target: powerButton.background
                        border.color: Qt.lighter(root.palette.highlight, 1.1)
                    }
                },
                State {
                    name: "focused"
                    when: powerButton.activeFocus
                    PropertyChanges {
                        target: powerButton
                        palette.buttonText: root.palette.highlight
                    }
                    PropertyChanges {
                        target: powerButton.background
                        border.color: root.palette.highlight
                    }
                }
            ]

            transitions: [
                Transition {
                    PropertyAnimation {
                        properties: "palette.buttonText, border.color"
                        duration: 150
                    }
                }
            ]
        }
    }
}

