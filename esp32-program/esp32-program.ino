#include <PZEM004Tv30.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <RTClib.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ================= WIFI CONFIG =================
const char* ssid = "AR NANI 2.4G";
const char* password = "AYAMlaos";
const char* serverName = "http://192.168.1.32:5000/api/sensor/data"; // UBAH KE IP PC ANDA

// ================= LCD =================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ================= RTC =================
RTC_DS3231 rtc;

// ================= PIN =================
#define RX1 26
#define TX1 27
#define RX2 32
#define TX2 33

// ================= SERIAL =================
HardwareSerial SerialPZEM1(2);
HardwareSerial SerialPZEM2(1);

// ================= PZEM =================
PZEM004Tv30 pzem1;
PZEM004Tv30 pzem2;

// ================= VAR =================
float v1,i1,p1,e1,f1,pf1;
float v2,i2,p2,e2,f2,pf2;

// ================= TIMER =================
unsigned long lastRead = 0;
unsigned long lastLCD  = 0;
unsigned long lastMode = 0;

int mode = 0;

// ================= FILTER =================
float safe(float val){ return isnan(val) ? 0 : val; }

// ================= INIT =================
void initPZEM(){
  Serial.println("RECONNECT PZEM...");
  SerialPZEM1.begin(9600, SERIAL_8N1, RX1, TX1);
  SerialPZEM2.begin(9600, SERIAL_8N1, RX2, TX2);

  pzem1 = PZEM004Tv30(SerialPZEM1, RX1, TX1);
  pzem2 = PZEM004Tv30(SerialPZEM2, RX2, TX2);

  delay(1000);
}

void initWiFi(){
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  initWiFi();
  initPZEM();

  lcd.init();
  lcd.backlight();

  if (!rtc.begin()) {
    Serial.println("RTC ERROR");
    // while (1); // Disable block for debug
  }

  lcd.setCursor(0,0);
  lcd.print("System Ready");
  delay(1500);
}

// ================= LOOP =================
void loop() {

  unsigned long nowMillis = millis();
  DateTime now = rtc.now();

  // ===== BACA SENSOR & KIRIM HTTP (Kirim tiap 3 detik demi efisiensi) =====
  if(nowMillis - lastRead >= 3000){
    lastRead = nowMillis;

    v1 = safe(pzem1.voltage());
    i1 = safe(pzem1.current());
    p1 = safe(pzem1.power());
    e1 = safe(pzem1.energy());
    f1 = safe(pzem1.frequency());
    pf1 = safe(pzem1.pf());

    v2 = safe(pzem2.voltage());
    i2 = safe(pzem2.current());
    p2 = safe(pzem2.power());
    e2 = safe(pzem2.energy());
    f2 = safe(pzem2.frequency());
    pf2 = safe(pzem2.pf());

    // LOGIKA MATI
    if (v1 < 50){ v1=0; i1=0; p1=0; }
    if (v2 < 50){ v2=0; i2=0; p2=0; }

    float totalPower  = p1 + p2;
    float totalEnergy = e1 + e2;

    // ===== SERIAL MONITOR =====
    Serial.println("\n==============================================");
    Serial.printf("WAKTU : %04d-%02d-%02d %02d:%02d:%02d\n",
      now.year(), now.month(), now.day(),
      now.hour(), now.minute(), now.second());

    Serial.println("==============================================");
    Serial.println("PARAMETER        | MESIN 1        | MESIN 2");
    Serial.println("------------------------------------------------");

    Serial.printf("Voltage (V)      | %-14.2f | %-14.2f\n", v1, v2);
    Serial.printf("Current (A)      | %-14.2f | %-14.2f\n", i1, i2);
    Serial.printf("Power (W)        | %-14.2f | %-14.2f\n", p1, p2);
    Serial.printf("Energy (kWh)     | %-14.3f | %-14.3f\n", e1, e2);
    Serial.printf("Frequency (Hz)   | %-14.1f | %-14.1f\n", f1, f2);
    Serial.printf("Power Factor     | %-14.2f | %-14.2f\n", pf1, pf2);

    Serial.println("------------------------------------------------");
    Serial.printf("TOTAL POWER      : %.2f W\n", totalPower);
    Serial.printf("TOTAL ENERGY     : %.3f kWh\n", totalEnergy);

    Serial.printf("STATUS           | %-14s | %-14s\n",
      (p1 > 0 ? "ON" : "OFF"),
      (p2 > 0 ? "ON" : "OFF"));
    
    // ===== HTTP POST KE SERVER LAOKAL Flask =====
    if(WiFi.status() == WL_CONNECTED){
      HTTPClient http;
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");

      String jsonPayload = String("{\"m1\": {") + 
                            "\"v\":" + String(v1) + ",\"i\":" + String(i1) + ",\"p\":" + String(p1) + 
                            ",\"e\":" + String(e1) + ",\"f\":" + String(f1) + ",\"pf\":" + String(pf1) + "}," +
                            "\"m2\": {" + 
                            "\"v\":" + String(v2) + ",\"i\":" + String(i2) + ",\"p\":" + String(p2) + 
                            ",\"e\":" + String(e2) + ",\"f\":" + String(f2) + ",\"pf\":" + String(pf2) + "}}";
                            
      int httpResponseCode = http.POST(jsonPayload);
      Serial.print("HTTP POST => => Response code: ");
      Serial.println(httpResponseCode);
      http.end();
    } else {
      Serial.println("WiFi Disconnected. Data not sent.");
    }
    Serial.println("==============================================\n");
  }

  // ===== GANTI MODE LCD (3 detik) =====
  if(nowMillis - lastMode >= 3000){
    lastMode = nowMillis;
    mode++;
    if(mode > 2) mode = 0;
  }

  // ===== UPDATE LCD (500 ms) =====
  if(nowMillis - lastLCD >= 500){
    lastLCD = nowMillis;

    char line1[17];
    char line2[17];

    if(mode == 0){
      snprintf(line1, sizeof(line1), "M1:%3.0f M2:%3.0f", p1, p2);
      snprintf(line2, sizeof(line2), "Tot:%4.0f W", p1+p2);
    }
    else if(mode == 1){
      snprintf(line1, sizeof(line1), "V1:%3.0f V2:%3.0f", v1, v2);
      snprintf(line2, sizeof(line2), "I1:%.1f I2:%.1f", i1, i2);
    }
    else{
      snprintf(line1, sizeof(line1), "E1:%.2f E2:%.2f", e1, e2);
      snprintf(line2, sizeof(line2), "%02d:%02d:%02d",
        now.hour(), now.minute(), now.second());
    }

    lcd.setCursor(0,0);
    lcd.print("                "); 
    lcd.setCursor(0,0);
    lcd.print(line1);

    lcd.setCursor(0,1);
    lcd.print("                "); 
    lcd.setCursor(0,1);
    lcd.print(line2);
  }
}
