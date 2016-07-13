/**
 * Receiving remote control commands via infrared sensors.
 * Author: Matheus V. Portela
 * GitHub: https://github.com/matheusportela/control-your-laptop
 */

#define DEBUG 1

// Microseconds between signals
#define SLEEP_TIME 1000

// Arduino pin to receive IR signals
int IRpin = 2;

// Buffer to store received IR data
byte receivedData[30];

// Implemented commands
byte PLAY_BUTTON[30]  = {1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0};
byte STOP_BUTTON[30]  = {1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0};
byte PAUSE_BUTTON[30] = {1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0};
byte BACK_BUTTON[30]  = {1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0};
byte FORW_BUTTON[30]  = {1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0};

void setup() {
  Serial.begin(115200);
  Serial.println("Control Your Laptop");
  Serial.print("Setting up... ");
  setupIRReceiver();
  Serial.println("done");
}

void recognizeButton() {
  int i;
  int isPlay = 1;
  int isStop = 1;
  int isPause = 1;
  int isBackward = 1;
  int isForward = 1;

  for (i = 0; i < 30; i++) {
    if (receivedData[i] != PLAY_BUTTON[i])
      isPlay = 0;
    if (receivedData[i] != STOP_BUTTON[i])
      isStop = 0;
    if (receivedData[i] != PAUSE_BUTTON[i])
      isPause = 0;
    if (receivedData[i] != BACK_BUTTON[i])
      isBackward = 0;
    if (receivedData[i] != FORW_BUTTON[i])
      isForward = 0;
  }
  
  if (isPlay)
    Serial.println("Play");
  else if (isStop)
    Serial.println("Stop");
  else if (isPause)
    Serial.println("Pause");
  else if (isBackward)
    Serial.println("Backward");
  else if (isForward)
    Serial.println("Forward");
  else
    Serial.println("Unrecognized button");
}

void loop() {
  Serial.println("Waiting for commands...");
  recvCommand();

  if (DEBUG) {
    int i;
    for (i = 0; i < 30; i++) {
      Serial.print(receivedData[i]);
      Serial.print(' ');
    }
    Serial.print('\n');
  }
  
  recognizeButton();
  delay(1000);
}
