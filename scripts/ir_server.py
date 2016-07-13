import serial
import os

def play():
    print 'Play'
    cmd = '''
    tell application "System Events"
      tell application "VLC" to activate
      delay(0.5)
      tell process "VLC" to keystroke space
    end tell
    '''
    os.system('osascript -e \'' + cmd + '\'')

def stop():
    print 'Stop'
    cmd = '''
    tell application "System Events"
      tell application "VLC" to activate
      delay(0.5)
      tell process "VLC" to key code 47 using command down
    end tell
    '''
    os.system('osascript -e \'' + cmd + '\'')

def pause():
    print 'Pause'
    cmd = '''
    tell application "System Events"
      tell application "VLC" to activate
      delay(0.5)
      tell process "VLC" to keystroke space
    end tell
    '''
    os.system('osascript -e \'' + cmd + '\'')

def backward():
    print 'Backward'
    cmd = '''
    tell application "System Events"
      tell application "VLC" to activate
      delay(0.5)
      tell process "VLC" to key code 123 using {command down, option down}
    end tell
    '''
    os.system('osascript -e \'' + cmd + '\'')

def forward():
    print 'Forward'
    cmd = '''
    tell application "System Events"
      tell application "VLC" to activate
      delay(0.5)
      tell process "VLC" to key code 124 using {command down, option down}
    end tell
    '''
    os.system('osascript -e \'' + cmd + '\'')

if __name__ == '__main__':
    arduino = serial.Serial('/dev/tty.usbmodem1431', 115200)
    while True:
        data = arduino.readline().rstrip('\r\n')
        if data == 'Play':
            play()
        elif data == 'Stop':
            stop()
        elif data == 'Pause':
            pause()
        elif data == 'Backward':
            backward()
        elif data == 'Forward':
            forward()
