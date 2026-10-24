import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Commons as Commons
import qs.Ui

Panel {
  id: root
  moduleName: "io.github.tw527e.howdy-manual"

  PanelWindow {
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "howdy-manual-preview"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore
    Rectangle { anchors.fill: parent; color: Commons.Color.polkit.scrim }
    PromptView {
      id: preview
      anchors.centerIn: parent
      message: tr("Preview only — no permissions will be granted.\nAuthentication is required to install software.", "僅為預覽，不會授予權限。\n安裝軟體需要驗證身份。")
      actionId: "org.freedesktop.packagekit.package-install"
      prompt: "Password (or press Enter for face recognition): "
      responseRequired: true
      onFaceRequested: supplementary = tr("Preview: the camera was not started.", "預覽：未啟動相機。")
      onPasswordSubmitted: supplementary = tr("Preview: this input was discarded.", "預覽：輸入內容已丟棄。")
      onCancelRequested: root.close()
    }
  }
}
