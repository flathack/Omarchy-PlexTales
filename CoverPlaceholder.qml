import QtQuick
import qs.Commons

// Simple book silhouette, also legible at bar size.
Item {
  id: root
  property color foreground: Color.accent

  Rectangle {
    anchors.centerIn: parent
    width: Math.max(1, Math.min(root.width, root.height) * 0.58)
    height: Math.max(1, Math.min(root.width, root.height) * 0.72)
    radius: Math.max(1, width * 0.08)
    color: "transparent"
    border.color: root.foreground
    border.width: Math.max(1, Math.round(width * 0.08))

    Rectangle {
      anchors.left: parent.left
      anchors.leftMargin: Math.max(2, parent.width * 0.19)
      anchors.verticalCenter: parent.verticalCenter
      width: Math.max(1, parent.width * 0.06)
      height: parent.height * 0.65
      color: root.foreground
    }
  }
}
