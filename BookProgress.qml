import QtQuick
import QtQuick.Layouts
import qs.Commons
import "Model.js" as Model

ColumnLayout {
  id: root
  property real elapsed: 0
  property real total: 0
  property color foreground: Color.popups.text
  property color muted: Qt.darker(foreground, 1.55)
  property string fontFamily: Style.font.family
  readonly property real safeTotal: Math.max(0, Number(total) || 0)
  readonly property real safeElapsed: Math.max(0, Math.min(safeTotal, Number(elapsed) || 0))
  readonly property real remaining: safeTotal - safeElapsed
  readonly property real percent: safeTotal > 0 ? Math.round(safeElapsed / safeTotal * 1000) / 10 : 0

  visible: safeTotal > 0
  spacing: Style.space(3)
  Accessible.role: Accessible.ProgressBar
  Accessible.name: "Audiobook progress: " + percent + "% · "
    + Model.formatTime(safeElapsed) + " heard · " + Model.formatTime(remaining) + " left"

  RowLayout {
    Layout.fillWidth: true
    spacing: Style.space(7)
    Text {
      textFormat: Text.PlainText
      text: "Heard " + Model.formatTime(root.safeElapsed)
      color: root.muted
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
    }
    Item { Layout.fillWidth: true }
    Text {
      textFormat: Text.PlainText
      text: "Left " + Model.formatTime(root.remaining)
      color: root.muted
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
    }
    Text {
      textFormat: Text.PlainText
      text: root.percent + "%"
      color: Color.accent
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
      font.bold: true
    }
  }

  Rectangle {
    Layout.fillWidth: true
    Layout.preferredHeight: Math.max(3, Style.space(4))
    radius: height / 2
    color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.17)

    Rectangle {
      anchors.left: parent.left
      anchors.top: parent.top
      anchors.bottom: parent.bottom
      width: parent.width * (root.safeTotal > 0 ? root.safeElapsed / root.safeTotal : 0)
      radius: height / 2
      color: Color.accent
    }
  }
}
