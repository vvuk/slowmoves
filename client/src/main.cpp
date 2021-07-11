#include <stdlib.h>

#include "Inkplate.h"
#include "WiFiClient.h"
#include "HTTPClient.h"

#include "wifi-secrets.h"

Inkplate display(INKPLATE_3BIT);

#define DELAY_MS 5000

#define SERVER_URL "http://192.168.17.10:8954/test.pgm"
#define ENCODE_PIXEL_VALUE(v)  ((v) >> 5)

void
setup()
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

    // TODO -- we may need to call begin in loop(), not sure where deep sleep comes back to
    display.begin();

    display.clearDisplay();
    display.display();

#if false
    display.setTextColor(0, 7);
    display.setCursor(250, 420);
    display.setTextSize(4);
    display.print("Connected to WiFi");
    display.display();
    delay(5000);
#endif
}

void fetchAndDrawOneFrame();

void loop()
{
    auto mstart = millis();
    fetchAndDrawOneFrame();
    auto mend = millis();

    Serial.printf("fetch and draw one frame took: %d ms\n", int(mend - mstart));
    delay(DELAY_MS);
}

// skip whitespace and comments, then
// read a number
uint32_t
read_next_pgm_header_item(char **pptr)
{
    char *ptr = *pptr;
    while (isspace(*ptr)) ptr++;
    if (*ptr == '#') {
        while (*ptr && *ptr != '\n') ptr++;
    }
    while (isspace(*ptr)) ptr++;

    char *ptr_out = ptr;
    uint32_t value = strtoul(ptr, &ptr_out, 10);
    if (ptr == ptr_out) {
        Serial.printf("Failed to read a number from header; header was: \n%32s\n", *pptr);
        return 0;
    }

    *pptr = ptr_out;
    return value;
}

void
fetchAndDrawOneFrame()
{
    WiFiClient wclient;
    HTTPClient http;

    http.begin(wclient, SERVER_URL);

    int httpCode = http.GET();
    Serial.printf("Got HTTP Code %d\n", httpCode);
    if (httpCode != 200) {
        return;
    }

    #define READ_BUF_SZ 4096
    //char readbuf[READ_BUF_SZ] = { 0 };
    static char *readbuf = (char*) malloc(READ_BUF_SZ);

    int data_len = http.getSize();
    Serial.printf("Got content-length %d\n", data_len);
    if (data_len == -1) {
        return;
    }

    uint32_t width = 0, height = 0, maxpix = 0;
    uint16_t src_x = 0, src_y = 0;

    display.clearDisplay();

    auto stream = http.getStream();
    while (http.connected() && data_len > 0)
    {
        auto avail = stream.available();
        //Serial.printf("Avail %d, remain %d\n", avail, data_len);
        while (avail > 0) {
            int readlen = stream.readBytes(readbuf, (avail > READ_BUF_SZ) ? READ_BUF_SZ : avail);
            //Serial.printf("  read %d\n", readlen);
            char* ptr = readbuf;
            if (maxpix == 0) {
                if (readlen < 64) {
                    Serial.printf("Expected at least 64 bytes, got %d\n", readlen);
                    return;
                }

                // read PGM header
                if (memcmp(ptr, "P5", 2) != 0) {
                    Serial.println("Expected P5 header");
                    return;
                }
                // skip P5
                ptr += 2;

                // this will absolutely blow up if there are comments (#...) in the PGM header that
                // are bigger than a single read buffer.  The actual server won't ever send these.
                width = read_next_pgm_header_item(&ptr);
                height = read_next_pgm_header_item(&ptr);
                maxpix = read_next_pgm_header_item(&ptr);
                ptr++;

                Serial.printf("Got PGM image %dx%d (max %d)\n", width, height, maxpix);
                if (maxpix != 255) {
                    return;
                }

                // ptr now has start of image bytes, or if we already have the header,
                // just continuing from where we left off
            }

            for (int i = 0; i < readlen; i++) {
                char val = *ptr++;
                if (src_x < E_INK_WIDTH && src_y < E_INK_HEIGHT) {
                    display.drawPixel(src_x, src_y, ENCODE_PIXEL_VALUE(val));
                }
                src_x++;
                if (src_x == width) {
                    src_y++;
                    src_x = 0;
                }
            }

            data_len -= readlen;
            avail -= readlen;
        }
    }

    http.end();

#if true
    // draw color bars
    int xoff = 100, yoff = 100;
    for (int j = 0; j < 128; j++)
    {
        for (int i = 0; i < 256; i++)
        {
            // Only 3 bits of color are supported, so i >> 5
            // But the colors are all shades of dark, and then the final white.
            // I think this can probably be optimized by messing with the "waveforms"?
            display.drawPixel(xoff + i, yoff + j, ENCODE_PIXEL_VALUE(i));
        }
    }
#endif

    display.display();
}
