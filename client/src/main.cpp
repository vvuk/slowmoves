#include <stdlib.h>

#include "Inkplate.h"
#include "WiFiClient.h"
#include "HTTPClient.h"

#include "wifi-secrets.h"

Inkplate display(INKPLATE_3BIT);

#define DELAY_MS 5000

void setup()
{
    // this should be the same as the boot loader baud rate, but I can't get boot data to show up in PIO's monitor, just garbage
    Serial.begin(115200);
    Serial.println("");
    Serial.println("Booting");

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    if (WiFi.waitForConnectResult() != WL_CONNECTED)
    {
      Serial.println("Failed to connect to WiFi");
    }

    display.begin();
    display.clearDisplay();
    display.display();

    display.setTextColor(0, 7);
    display.setCursor(250, 420);
    display.setTextSize(4);
    display.print("Connected to WiFi");
    display.display();
    delay(5000);
}

void loop()
{
    WiFiClient wclient;
    HTTPClient http;

    http.begin(wclient, "http://micropython.org/ks/test.html");
    int httpCode = http.GET();
    int contentLength = http.getString().length();
    http.end();

    display.clearDisplay();
    char ss[256];
    snprintf(ss, 256, "HTTP reponse %d got %d content-length", httpCode, contentLength);
    display.setTextSize(2);
    display.setCursor(2, 810);
    display.print(ss);

    // there is nothing to be gained by calling drawImage.  It literally loops and calls drawPixel(x, y, value) for each pixel.
    //display.drawImage(image, 100, 100, 256, 256);

    int xoff = 100, yoff = 100;
    for (int j = 0; j < 256; j++) {
      for (int i = 0; i < 256; i++) {
        // Only 3 bits of color are supported, so i >> 5
        // But the colors are all shades of dark, and then the final white.
        // I think this can probably be optimized by messing with the "waveforms"?
        display.drawPixel(xoff + i, yoff + j, i >> 5);
      }
    }

    display.display();
    delay(DELAY_MS);
}
