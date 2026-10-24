import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "Model.js" as Model

BorderSurface {
  id: root

  property string fontFamily: language.toLowerCase().indexOf("zh") === 0 ? "Noto Sans CJK TC" : "sans-serif"
  property string language: Qt.locale().name
  property string message: ""
  property string actionId: ""
  property string prompt: ""
  property string supplementary: ""
  property bool responseRequired: false
  property bool responseVisible: false
  property bool busy: false
  property bool failed: false
  property bool scanning: false
  property real availableHeight: 800
  readonly property bool faceChoice: responseRequired && Model.isFaceChoice(prompt)
  readonly property color foreground: Commons.Color.polkit.text
  readonly property color accent: Commons.Color.polkit.accent
  readonly property int controlHeight: Math.max(44, Style.spacing.controlHeight)
  signal passwordSubmitted(string value)
  signal faceRequested()
  signal cancelRequested()

  function tr(en, zh) { return Model.text(en, zh, language) }
  function clear() { password.text = "" }
  function focusInput() { password.forceActiveFocus() }
  function submit() {
    if (!Model.canSubmit(responseRequired, busy, faceChoice, password.text)) return
    var value = password.text
    password.text = ""
    root.passwordSubmitted(value)
  }

  width: Math.min(480, parent ? parent.width - 32 : 480)
  implicitHeight: content.implicitHeight + contentTopInset + contentBottomInset
  height: implicitHeight
  padding: Style.space(24)
  color: Commons.Color.polkit.background
  radius: Style.cornerRadius
  borderSpec: Border.surfaceSpec("polkit", "border", Commons.Color.polkit.border, 1, "border-alpha")
  Keys.onEscapePressed: root.cancelRequested()

  Column {
    id: content
    x: root.contentLeftInset
    y: root.contentTopInset
    width: root.width - root.contentLeftInset - root.contentRightInset
    spacing: Style.space(16)

    Text {
      width: parent.width
      text: root.tr("Authorize action", "確認授權")
      textFormat: Text.PlainText
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Math.max(20, Style.font.subtitle)
      font.bold: true
      wrapMode: Text.WordWrap
    }

    Flickable {
      width: parent.width
      height: Math.min(details.implicitHeight, Math.max(64, root.availableHeight * 0.25))
      contentHeight: details.implicitHeight
      clip: true
      boundsBehavior: Flickable.StopAtBounds
      flickableDirection: Flickable.VerticalFlick
      Text {
        id: details
        width: parent.width
        text: root.message
        textFormat: Text.PlainText
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: Math.max(14, Style.font.body)
        wrapMode: Text.Wrap
      }
    }

    Text {
      width: parent.width
      visible: root.actionId.length > 0
      text: root.actionId
      textFormat: Text.PlainText
      color: root.foreground
      opacity: 0.75
      font.family: root.fontFamily
      font.pixelSize: Math.max(12, Style.font.bodySmall)
      wrapMode: Text.WrapAnywhere
    }

    Button {
      width: parent.width
      height: root.controlHeight
      visible: root.faceChoice || root.scanning
      text: root.scanning ? root.tr("Looking for you…", "正在辨識…") : root.tr("Use face recognition", "使用臉部辨識")
      enabled: root.faceChoice && !root.busy
      focusable: true
      bordered: true
      foreground: root.foreground
      selected: true
      fontFamily: root.fontFamily
      accent: root.accent
      fontSize: Math.max(14, Style.font.body)
      onClicked: { root.clear(); root.faceRequested() }
      Accessible.role: Accessible.Button
      Accessible.name: text
    }

    Text {
      width: parent.width
      visible: root.faceChoice && !root.busy
      text: root.tr("The camera stays off until you choose face recognition.", "按下臉部辨識按鈕後，才會啟動相機。")
      textFormat: Text.PlainText
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: Math.max(12, Style.font.bodySmall)
      wrapMode: Text.WordWrap
    }

    Column {
      width: parent.width
      spacing: Style.space(8)
      Text {
        width: parent.width
        text: root.scanning ? root.tr("Password entry is available after the face scan finishes.", "臉部辨識結束後，即可使用密碼驗證。")
          : root.faceChoice ? root.tr("Or enter your password", "或輸入密碼") : (root.prompt || root.tr("Password", "密碼"))
        textFormat: Text.PlainText
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: Math.max(14, Style.font.body)
        wrapMode: Text.WordWrap
      }
      BorderSurface {
        width: parent.width
        height: root.controlHeight
        radius: Style.cornerRadius
        color: "transparent"
        borderSpec: Border.controlSpec(password.activeFocus ? "focus" : "normal", root.foreground, root.accent)
        TextInput {
          id: password
          objectName: "passwordInput"
          anchors.fill: parent
          anchors.margins: Style.space(12)
          verticalAlignment: TextInput.AlignVCenter
          clip: true
          color: root.foreground
          font.family: root.fontFamily
          font.pixelSize: Math.max(16, Style.font.body)
          echoMode: root.responseVisible ? TextInput.Normal : TextInput.Password
          passwordCharacter: "\u2022"
          selectByMouse: true
          activeFocusOnTab: true
          readOnly: root.busy || !root.responseRequired
          selectionColor: Util.alpha(root.accent, 0.45)
          selectedTextColor: root.foreground
          onAccepted: root.submit()
          Accessible.role: Accessible.EditableText
          Accessible.name: root.tr("Authentication response", "驗證輸入")
        }
      }
    }

    Text {
      width: parent.width
      visible: text.length > 0
      text: root.failed ? root.tr("Authentication failed. Try again.", "驗證失敗，請重試。")
        : root.supplementary || (root.busy && !root.scanning ? root.tr("Checking…", "驗證中…") : "")
      textFormat: Text.PlainText
      color: root.foreground
      font.bold: root.failed
      font.family: root.fontFamily
      font.pixelSize: Math.max(14, Style.font.body)
      wrapMode: Text.Wrap
    }

    Row {
      width: parent.width
      spacing: Style.space(12)
      Button {
        width: (parent.width - parent.spacing) / 2
        height: root.controlHeight
        text: root.tr("Cancel", "取消")
        focusable: true
        fontFamily: root.fontFamily
        fontSize: Math.max(14, Style.font.body)
        bordered: false
        onClicked: root.cancelRequested()
        Accessible.role: Accessible.Button
        Accessible.name: text
      }
      Button {
        width: (parent.width - parent.spacing) / 2
        height: root.controlHeight
        text: root.tr("Authenticate", "驗證")
        enabled: Model.canSubmit(root.responseRequired, root.busy, root.faceChoice, password.text)
        focusable: true
        fontFamily: root.fontFamily
        fontSize: Math.max(14, Style.font.body)
        bordered: true
        onClicked: root.submit()
        Accessible.role: Accessible.Button
        Accessible.name: text
      }
    }
  }
}
