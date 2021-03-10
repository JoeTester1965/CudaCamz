//
// Will need an Arduino IDE, esp8266, an 8x8 ws2312b matrix and a bit of solder to hand
//

#include <gamma.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include <WiFiManager.h>     
#include <PubSubClient.h>

const char* mqtt_server = "a.b.c.d";
const char* mqtt_username = "username";
const char* mqtt_password = "password";
const char*cudacam_topic = "CudaCam";
 
#define DISPLAY_PIN    D7

struct RGB {
  byte r;
  byte g;
  byte b;
};

// Define some colors we'll use frequently
RGB white = { 255, 255, 255 };
RGB red = { 255, 0, 0 };
RGB green = { 0, 255, 0 };
RGB blue = { 0, 0, 255 };
RGB off = { 0, 0, 0 };

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(8, 8, 1, 1, DISPLAY_PIN,
    NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
    NEO_GRB + NEO_KHZ800);

WiFiClient espClient;
PubSubClient client(espClient);

#define MAX_MESSAGES    5
#define BUFFER_SIZE     256

typedef struct message_in_q
{
    byte message[BUFFER_SIZE];
};

typedef struct message_q
{
    int messages_in_queue;
    int index_in;
    int index_out;
    struct message_in_q messages[MAX_MESSAGES];
};

struct message_q* queue;

struct message_q* list_initialise(void);
struct message_in_q* manage_list(struct message_q* list);
void add_to_list(struct message_q* list, byte* data, uint64_t flags, unsigned int length);

void callback(char* topic, byte* payload, unsigned int length) 
{
    payload[length] = 0;

    add_to_list(queue, payload, length);
}

struct message_q* list_initialise(void)
{
    struct message_q* retval = NULL;

    retval = (message_q*)malloc(sizeof(struct message_q));

    retval->messages_in_queue = 0;
    retval->index_in = 0;
    retval->index_out = 0;

    for (int index = 0; index < MAX_MESSAGES; index++)
    {
        struct message_in_q* item = &retval->messages[index];
        item->message[0] = 0;
    }

    return retval;
}

void add_to_list(struct message_q* list, byte* data, unsigned int length)
{
    list->messages_in_queue++;
    if (list->messages_in_queue >= MAX_MESSAGES)
    {
        list->messages_in_queue = MAX_MESSAGES;
    }

    if (length > BUFFER_SIZE)
    {
        length = BUFFER_SIZE - 1;
    }
    memcpy(&list->messages[list->index_in].message[0], data, length);
    list->messages[list->index_in].message[length] = 0;

    list->index_in++;
    if (list->index_in >= MAX_MESSAGES)
    {
        list->index_in = 0;
    }
}

struct message_in_q* manage_list(struct message_q* list)
{
    struct message_in_q* retval = NULL;

    if (list->messages_in_queue > 0)
    {
        retval = &list->messages[list->index_out];

        list->messages_in_queue--;
        list->index_out++;

        if (list->index_out >= MAX_MESSAGES)
        {
            list->index_out = 0;
        }
    }

    return retval;
}


void reconnect() 
{
    while (!client.connected()) 
    {
        Serial.printf("Attempting MQTT connection to %s as %s\n", mqtt_server, mqtt_username);
        String clientId = "ESP8266Client-";
        clientId += String(random(0xffff), HEX);
        if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) 
        {
            Serial.printf("MQTT connected\n");
            client.subscribe(cudacam_topic);
        }
        else 
        {
            Serial.printf("MQTT connection failed, sleeping for 5 seconds\n");
            delay(5000);
        }
    }
}

void scrollText(String textToDisplay, uint16_t colour)
{
    int x = matrix.width();

    textToDisplay = "-> " + textToDisplay + " ";
    int pixelsInText = textToDisplay.length() * 7;

    matrix.clear();
    matrix.setTextColor(colour);
    matrix.setCursor(x, 0);
    matrix.print(textToDisplay);
    matrix.show();

    while (x > (matrix.width() - pixelsInText))
    {
        matrix.fillScreen(matrix.Color(off.r, off.g, off.b));
        matrix.setCursor(--x, 0);
        matrix.print(textToDisplay);
        matrix.show();
        delay(100);
        client.loop();
    }

    matrix.clear();
}

void setup() 
{
    Serial.begin(115200);
    delay(10);
    Serial.println("");
    WiFiManager wifiManager;
    wifiManager.autoConnect();
    Serial.printf("Connected with IP %s\n", WiFi.localIP().toString().c_str());
    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
    matrix.begin();
    matrix.setRotation(2);
    matrix.setTextWrap(false);
    matrix.setBrightness(40);
    matrix.fillScreen(0);
    queue = list_initialise();
}

void loop()
{
    struct message_in_q* message = NULL;
    
    if (!client.connected())
    {
        reconnect();
    }
    client.loop();

    message = manage_list(queue);

    if (message != NULL)
    {
        Serial.printf("Have a MQTT message to display -> %s\n", &message->message[0]);
        scrollText((char*)&message->message[0], matrix.Color(0, 0, 255));
    }

}
