.pragma library

var MAX_PENDING_ACTIONS = 8

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, Number(value) || 0))
}

function formatTime(seconds) {
  var value = Math.max(0, Math.floor(Number(seconds) || 0))
  var hours = Math.floor(value / 3600)
  var minutes = Math.floor(value / 60)
  var rest = value % 60
  if (hours) return hours + ":" + ((minutes % 60) < 10 ? "0" : "") + (minutes % 60) + ":" + (rest < 10 ? "0" : "") + rest
  return minutes + ":" + (rest < 10 ? "0" : "") + rest
}

function barLabel(status) {
  if (!status || !status.configured) return "\uf02d"
  if (!status.track || !status.track.title) return "\uf02d"
  return (status.playing ? "\uf04c  " : "\uf04b  ") + (status.track.album || status.track.title)
}

function safeArray(value) {
  return Array.isArray(value) ? value : []
}

function subtitle(item) {
  if (!item) return ""
  var artist = String(item.artist || "")
  var album = String(item.album || "")
  if (artist && album && artist !== album) return artist + " · " + album
  return artist || album
}

function defaultView(status) {
  return status && (status.playing === true || status.paused === true) ? "queue" : "continue"
}

function navigationState(view, key, kind, title, query, selectedIndex) {
  return {
    view: String(view || "recent"),
    parentKey: String(key || ""),
    parentKind: String(kind || ""),
    title: String(title || ""),
    query: String(query || ""),
    selectedIndex: Math.max(0, Number(selectedIndex) || 0)
  }
}

function navigationArgs(state, recentLimit, libraryLimit) {
  var previous = state || navigationState("recent")
  if (previous.view === "children")
    return ["children", previous.parentKind, previous.parentKey]
  if (previous.view === "search")
    return ["search", previous.query, "--limit", "35"]
  if (previous.view === "queue") return ["queue"]
  return ["library", previous.view, "--limit",
          String(previous.view === "recent" ? recentLimit : libraryLimit)]
}

function actionKind(command) {
  var values = safeArray(command)
  for (var index = 0; index < values.length - 1; index++)
    if (values[index] === "control") return String(values[index + 1])
  return "transport"
}

function queueAction(pending, nextCommand) {
  var queued = safeArray(pending)
  var kind = actionKind(nextCommand)
  if (kind !== "seek" && kind !== "volume")
    return queued.concat([nextCommand]).slice(-MAX_PENDING_ACTIONS)
  var retained = []
  for (var index = 0; index < queued.length; index++)
    if (actionKind(queued[index]) !== kind) retained.push(queued[index])
  return retained.concat([nextCommand]).slice(-MAX_PENDING_ACTIONS)
}
