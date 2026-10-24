import QtQuick
import Quickshell
import Quickshell.Services.Polkit as Polkit
import Quickshell.Wayland
import qs.Commons as Commons
import "Model.js" as Model

Item {
  id: root
  property bool submitted: false
  property bool scanning: false
  property bool failed: false

  function clear() {
    submitted = false
    scanning = false
    failed = false
    view.clear()
  }

  Polkit.PolkitAgent {
    id: agent
    path: "/org/omarchy/HowdyManual"
    onAuthenticationRequestStarted: { root.clear(); Qt.callLater(view.focusInput) }
    onIsActiveChanged: if (!isActive) root.clear()
    onIsRegisteredChanged: {
      if (isRegistered) console.log("Howdy Manual: Polkit agent registered")
      else console.warn("Howdy Manual: Polkit agent unregistered; check for another agent")
    }
  }

  Connections {
    target: agent.flow
    function onIsResponseRequiredChanged() {
      if (agent.flow && agent.flow.isResponseRequired) {
        root.submitted = false
        root.scanning = false
        view.clear()
        Qt.callLater(view.focusInput)
      }
    }
    function onAuthenticationFailed() { root.clear(); root.failed = true }
    function onAuthenticationRequestCancelled() { root.clear() }
    function onAuthenticationSucceeded() { root.clear() }
  }

  PanelWindow {
    id: panel
    visible: agent.isActive
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-polkit"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore

    Rectangle { anchors.fill: parent; color: Commons.Color.polkit.scrim }
    Flickable {
      anchors.fill: parent
      anchors.margins: 16
      contentHeight: Math.max(height, view.height + 32)
      clip: true
      boundsBehavior: Flickable.StopAtBounds
      PromptView {
        id: view
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.max(16, (panel.height - height - 32) / 2)
        availableHeight: panel.height
        message: agent.flow ? agent.flow.message : ""
        actionId: agent.flow ? agent.flow.actionId : ""
        prompt: agent.flow ? agent.flow.inputPrompt : ""
        supplementary: agent.flow ? agent.flow.supplementaryMessage : ""
        responseRequired: !!agent.flow && agent.flow.isResponseRequired
        responseVisible: !!agent.flow && agent.flow.responseVisible
        busy: root.submitted
        scanning: root.scanning
        failed: root.failed
        onPasswordSubmitted: function(value) {
          if (!agent.flow || !Model.canSubmit(responseRequired, root.submitted, faceChoice, value)) return
          root.submitted = true
          root.failed = false
          agent.flow.submit(value)
        }
        onFaceRequested: {
          if (!agent.flow || !faceChoice || root.submitted) return
          root.submitted = true
          root.scanning = true
          root.failed = false
          agent.flow.submit("")
        }
        onCancelRequested: {
          view.clear()
          if (agent.flow) agent.flow.cancelAuthenticationRequest()
        }
      }
    }
  }
}
