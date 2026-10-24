function isFaceChoice(prompt) {
  return prompt === "Password (or press Enter for face recognition): "
}

function canSubmit(responseRequired, busy, faceChoice, value) {
  return responseRequired && !busy && (!faceChoice || value.length > 0)
}

function text(english, chinese, language) {
  return String(language).toLowerCase().indexOf("zh") === 0 ? chinese : english
}

if (typeof module !== "undefined") module.exports = { isFaceChoice, canSubmit, text }
