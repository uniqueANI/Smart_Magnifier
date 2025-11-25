const int trigPin = 2;
const int echoPin = 3;

void setup() {
  Serial.begin(115200);   // match app speed
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

long measureDistanceCM() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000UL);
  long distance = duration * 0.034 / 2;
  return distance;
}

void loop() {
  long d = measureDistanceCM();
  if (d > 0) {
    Serial.print("D,");
    Serial.println(d);   // <-- EXACT format app expects
  }
  delay(200);
}
