#include <SoftwareSerial.h>
#define LED 7
#define RxD 2
#define TxD 3
#define Vo A5

int per_hour_counter = 0;  // 100 samplings per second -> 3600 * 100 per hour
int per_day_counter = 0;  // 24 per_hour average
static float density_per_hour = 0;
static float density_per_day = 0;
static float hourly_avg = 0;
static float daily_avg = 0;

// zero-dust value in volts (calibrated with aerlive.ro measurements)
static float Voc = 1.15;

// typical sensitivity in units of V per 100ug/m3
const float K = 0.5;

// for verbose output
char output_mode;

SoftwareSerial BTSerial(RxD, TxD);

void printVo(float Vo) {
  float dVo = Vo - Voc, dust_dens;

  if (dVo < 0) {
    dVo = 0;
    Voc = Vo;  
  }

  dust_dens = dVo / K * 100.0;
  density_per_hour += dust_dens;
  per_hour_counter++;

  if (per_hour_counter == 360) {
    // one hour worth of data; make hourly average
    hourly_avg = density_per_hour / 360;//000;
    BTSerial.print("Hourly average: ");
    BTSerial.print(hourly_avg);
    BTSerial.println("ug/m3");
    density_per_hour = 0;
    per_hour_counter = 0;
    
    density_per_day += hourly_avg;
    per_day_counter++;

    if (per_day_counter == 24) {
      daily_avg = density_per_day / 24;
      BTSerial.print("Daily average: ");
      BTSerial.print(daily_avg);
      BTSerial.println("ug/m3");
      density_per_day = 0;
      per_day_counter = 0;
    }
  }

  if (output_mode == 'v') {
    BTSerial.print("Recorded: ");
    BTSerial.print(dust_dens);
    BTSerial.println("ug/m3");
  }
}

ISR(TIMER1_COMPA_vect) {
  // interrupt code for Timer1
  //Serial.println("timer1");
}

void setup() {
  // put your setup code here, to run once:

  // set timer1 to count up to 4s
  cli();  // stop interrupts while configuring

  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  
  OCR1A = 15624;//62499;  // 16MHz/1024prescaler/0.25Hz - 1
  TCCR1B |= (1 << WGM12);  // CTC mode
  TCCR1B |= (1 << CS12) | (1 << CS10);  // 1024 prescaler
  TIMSK1 |= (1 << OCIE1A);  // enable timer1 interrupts
  sei();  // enable global interrupts
  
  pinMode(LED, OUTPUT);
  Serial.begin(9600);
  BTSerial.begin(9600);

  // wait for start-up
  delay(2000);
  Serial.println("Inspector PM");
  Serial.println("............");

  output_mode = 'n';
}

void loop() {
  // put your main code here, to run repeatedly:
  if (BTSerial.available()){
    char c = BTSerial.read();
    Serial.write(c);
    
    switch (c) {
        case 'n':
        case 'v':
            // (non-)verbose output
            output_mode = c;
            break;
        default:
            break;
    }
  }

  if (Serial.available()) {
    BTSerial.write(Serial.read());
  }
  
  digitalWrite(LED, LOW);

  // sampling time (from datasheet)
  delayMicroseconds(280);

  int Vo_read = analogRead(Vo);

  if (output_mode == 'v') {
    BTSerial.print("Value read: ");
    BTSerial.print((float)Vo_read);
    BTSerial.print("\t");
  }
  
  digitalWrite(LED, HIGH);

  // wait for remainder of the 10ms cycle
  delayMicroseconds(9620);
  float Vo_read_f = (float)Vo_read / 1024.0 * 5.0;

  if (output_mode == 'v') {
    BTSerial.print("Raw voltage: ");
    BTSerial.print(Vo_read_f * 1000.0);
    BTSerial.print("mV\t");
  }
  
  printVo(Vo_read_f);
}
