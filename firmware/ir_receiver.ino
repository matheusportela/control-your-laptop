/**
 * Infrared receiver module.
 * Author: Matheus V. Portela
 * GitHub: https://github.com/matheusportela/control-your-laptop
 * 
 * References:
 * http://playground.arduino.cc/Code/InfraredReceivers
 */

#include <avr/interrupt.h>
#include <avr/io.h>

#define SAMPLE_SIZE 64

/**
 * Setting up IR receiver registers.
 * 
 * References:
 * http://www.avrbeginners.net/architecture/timers/timers.html
 * http://sphinx.mythic-beasts.com/~markt/ATmega-timers.html
 */
void setupIRReceiver() {
  // Setting up Timer/Counter Control register TCCR1A:
  // |    7   |    6   |    5   |    4   |    3   |    2   |    1   |    0   |
  // | COM1A1 | COM1A0 | ------ | ------ | ------ | ------ |  PWM11 |  PWM10 |
  //
  // COM1A1/COM1A0: Compare Output Mode bits 1/0; These bits control if and how the Compare Output pin is connected to Timer1.
  // With these bit you can connect the OC1 Pin to the Timer and generate pulses based on the timer.
  //
  // | COM1A1 | COM1A0 | Compare Output Mode
  // |    0   |    0   | Disconnect Pin OC1 from Timer/Counter 1
  // |    0   |    1   | Toggle OC1 on compare match
  // |    1   |    0   | Clear OC1 on compare match
  // |    1   |    1   | Set OC1 on compare match
  //
  // PWM11/PWM10: Pulse Width Modulator select bits; These bits select if Timer1 is a PWM and it's resolution from 8 to 10 bits:
  //
  // | PWM11 | PWM10 | PWM Mode
  // |   0   |   0   | PWM operation disabled
  // |   0   |   1   | Timer/Counter 1 is an 8-bit PWM
  // |   1   |   0   | Timer/Counter 1 is a 9-bit PWM
  // |   1   |   1   | Timer/Counter 1 is a 10-bit PWM
  //
  // Since we want to disconnect Pin OC1 from Timer/Counter 1 and disable PWM operation, we set TCCR1A to 0.
  TCCR1A = 0x00;

  // Setting up Timer/Counter Control register TCCR1B:
  // |   7   |   6   |   5   |   4   |   3   |   2   |   1   |   0   |
  // | ICNC1 | ICES1 | ----- | ----- |  CTC1 |  CS12 |  CS11 |  CS10 |
  //
  // ICNC1: Input Capture Noise Canceler; If set, the Noise Canceler on the ICP pin is activated. It will trigger the input capture
  //        after 4 equal samples. The edge to be triggered on is selected by the ICES1 bit.
  // ICES1: Input Capture Edge Select; When cleared, the contents of TCNT1 are transferred to ICR (Input Capture Register) on the
  //        falling edge of the ICP pin. If set, the contents of TCNT1 are transferred on the rising edge of the ICP pin.
  // CTC1: Clear Timer/Counter 1 on Compare Match; If set, the TCNT1 register is cleared on compare match. Use this bit to create
  //       repeated Interrupts after a certain time, e.g. to handle button debouncing or other frequently occuring events. Timer 1
  //       is also used in normal mode, remember to clear this bit when leaving compare match mode if it was set. Otherwise the timer
  //       will never overflow and the timing is corrupted.
  // CS12..10: Clock Select bits; These three bits control the prescaler of timer/counter 1 and the connection to an external clock on Pin T1.
  // | CS12 | CS11 | CS10 | Mode Description
  // |   0  |   0  |   0  | Stop Timer/Counter 1
  // |   0  |   0  |   1  | No Prescaler (Timer Clock = System Clock)
  // |   0  |   1  |   0  | Divide clock by 8
  // |   0  |   1  |   1  | Divide clock by 64
  // |   1  |   0  |   0  | Divide clock by 256
  // |   1  |   0  |   1  | Divide clock by 1024
  // |   1  |   1  |   0  | Increment timer 1 on T1 Pin falling edge
  // |   1  |   1  |   1  | Increment timer 1 on T1 Pin rising edge
  //
  // Since our clock is about 16MHz, dividing it by 64 means incrementing TCNT1 every 4us.
  TCCR1B = 0x03;

  // Setting up Timer Interrupt Mask Register:
  // The Timer Interrupt Mask Register (TIMSK) and Timer Interrupt Flag (TIFR) Register are used to control which interrupts are "valid"
  // by setting their bits in TIMSK and to determine which interrupts are currently pending (TIFR).
  // |    7   |    6   |    5   |    4   |    3   |    2   |    1   |    0   |
  // |  TOIE1 | OCIE1A | ------ | ------ | TICIE1 | ------ |  TOIE0 | ------ |
  //
  // TOIE1: Timer Overflow Interrupt Enable (Timer 1); If this bit is set and if global interrupts are enabled, the micro will jump to the
  //        Timer Overflow 1 interrupt vector upon Timer 1 Overflow.
  // OCIE1A: Output Compare Interrupt Enable 1 A; If set and if global Interrupts are enabled, the micro will jump to the Output Compare A
  //         Interrupt vetor upon compare match.
  // TICIE1: Timer 1 Input Capture Interrupt Enable; If set and if global Interrupts are enabled, the micro will jump to the Input Capture
  //         Interrupt vector upon an Input Capture event.
  // TOIE0: Timer Overflow Interrupt Enable (Timer 0); Same as TOIE1, but for the 8-bit Timer 0.
  //
  // Let' disable all interrupts here.
  TIMSK1 = 0x00;

  // Setting up infrared pin as an input pin.
  pinMode(IRpin, INPUT);
}

/**
 * Compares whether received cyles is close to a given reference, considering an error margin.
 */
bool isNear(long cycles, long reference) {
  // Number of cycles for error margin, manually adjusted.
  const long errorMargin = 100;

  if (cycles < reference + errorMargin && cycles > reference - errorMargin)
    return true;
  return false;
}

/**
 * Given the duration which the transmission remained in HIGH level, demodulates to either 0 or 1.
 * We are assuming that the remote control uses a Pulse Length Coding protocol to encode 0's and 1's.
 * This might not be the case for all remote controls, then we'll need to evolve this function to better generalize to other controls.
 * 
 * References:
 * http://irq5.io/2012/07/27/infrared-remote-control-protocols-part-1/
 */
int demodulate(long duration) {
  // Number of cycles the pulse is HIGH for 0 bit, manually adjusted.
  const long zeroDuration = 500;

  // Number of cycles the pulse is HIGH for 1 bit, manually adjusted.
  const long oneDuration = 1600;
  
  if (isNear(duration, zeroDuration))
    return 0;
  else if (isNear(duration, oneDuration))
    return 1;
  return -1;
}

/**
 * Reset timer counter.
 */
void reset_timer() {
  TCNT1 = 0;
}

/**
 * Receive remote control command.
 * This function blocks until a distinguishable command is received by the sensor.
 */
void recvCommand() {
  byte change_count = 0;
  unsigned int timer_value[SAMPLE_SIZE];
  byte previous_level;
  long current_time;
  long previous_time;
  long duration;
  int demodulated_value;
  byte received_count;

  // Blocks until receiving the first HIGH signal. This indicates a remote control command is
  // about to be received.
  while(digitalRead(IRpin) == HIGH) {}
  
  reset_timer();
  timer_value[change_count] = TCNT1;
  previous_level = HIGH;
  change_count++;
  while (change_count < SAMPLE_SIZE) {
    if (previous_level == HIGH) {
      while (digitalRead(IRpin) == LOW) {}
      timer_value[change_count] = TCNT1;
      previous_level = LOW;
      change_count++;
    } else {
      while (digitalRead(IRpin) == HIGH) {}
      timer_value[change_count] = TCNT1;
      previous_level = HIGH;
      change_count++;
    }
  }

  // Transmits bits through serial output
  // Keep in mind that it always starts in LOW,
  // i.e., the first timer value is always w.r.t. 0.
  if (DEBUG) {
    Serial.println("START");
    
    int i;
    for (i = 0; i < SAMPLE_SIZE - 1; i++)
      Serial.println(timer_value[i]);
    
    Serial.println("END");
  }
}
