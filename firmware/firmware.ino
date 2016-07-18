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

void setup() {
  Serial.begin(115200);
  Serial.println("Control Your Laptop");
  Serial.print("Setting up... ");
  setupIRReceiver();
  Serial.println("done");
}

void loop() {
  recvCommand();
  delay(1000);
}
