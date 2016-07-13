tell application "System Events"
  tell application "VLC" to activate
  delay(0.5)
  tell process "VLC" to key code 124 using {command down, option down}
end tell
