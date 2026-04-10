from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivy.core.window import Window
from kivy.clock import mainthread, Clock
import paho.mqtt.client as mqtt
import ssl
import os
import json
import threading

# =========================
# MQTT CONFIG
# =========================
PORT = 8883  # TLS Port
KEEP_ALIVE = 10  # seconds
RECONNECT_DELAY = 1  # seconds

Window.size = (900, 700)

# =========================
# UI DESIGN
# =========================
KV = '''
#:kivy 2.0
'''

# =========================
# CONFIG SCREEN
# =========================
class ConfigScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'config'

# =========================
# FPI SCREEN
# =========================
class FPIScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'fpi'

# =========================
# MAIN APP
# =========================
class MainApp(MDApp):
    client = None
    is_connected = False
    current_imei = None
    ca_cert = None
    client_cert = None
    key_file = None

    def build(self):
        Builder.load_string(KV)
        
        self.screen_manager = ScreenManager()
        
        config_screen = ConfigScreen()
        fpi_screen = FPIScreen()
        
        self.screen_manager.add_widget(config_screen)
        self.screen_manager.add_widget(fpi_screen)
        
        self.build_config_screen(config_screen)
        self.build_fpi_screen(fpi_screen)
        
        self.screen_manager.current = 'config'
        
        return self.screen_manager

    def build_config_screen(self, config_screen):
        """Build the MQTT Configuration Screen"""
        config_screen.clear_widgets()
        
        main_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        title = MDLabel(text="[b]MQTT Configuration[/b]", markup=True, size_hint_y=None, height=40)
        main_layout.add_widget(title)
        
        # Scrollable area for form
        scroll = MDScrollView(size_hint=(1, 0.85))
        form_layout = MDGridLayout(cols=1, spacing=15, size_hint_y=None, padding=10)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # Project URL
        self.config_project_url = MDTextField(
            hint_text="Project URL",
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_project_url)
        
        # Username
        self.config_username = MDTextField(
            hint_text="Username",
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_username)
        
        # Password
        self.config_password = MDTextField(
            hint_text="Password",
            password=True,
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_password)
        
        # CA Certificate Path
        cert_layout = MDBoxLayout(size_hint_y=None, height=45, spacing=10)
        self.config_ca_cert = MDTextField(
            hint_text="CA Certificate Path (or paste here)",
            mode="rectangle",
            size_hint_x=0.7
        )
        cert_browse_btn = MDRaisedButton(
            text="Browse",
            size_hint_x=0.3,
            on_press=lambda: self.browse_certificate('ca')
        )
        cert_layout.add_widget(self.config_ca_cert)
        cert_layout.add_widget(cert_browse_btn)
        form_layout.add_widget(cert_layout)
        
        # Client Certificate Path
        client_cert_layout = MDBoxLayout(size_hint_y=None, height=45, spacing=10)
        self.config_client_cert = MDTextField(
            hint_text="Client Certificate Path (or paste here)",
            mode="rectangle",
            size_hint_x=0.7
        )
        client_cert_browse_btn = MDRaisedButton(
            text="Browse",
            size_hint_x=0.3,
            on_press=lambda: self.browse_certificate('client')
        )
        client_cert_layout.add_widget(self.config_client_cert)
        client_cert_layout.add_widget(client_cert_browse_btn)
        form_layout.add_widget(client_cert_layout)
        
        # Private Key Path
        key_layout = MDBoxLayout(size_hint_y=None, height=45, spacing=10)
        self.config_key_file = MDTextField(
            hint_text="Private Key Path (or paste here)",
            mode="rectangle",
            size_hint_x=0.7
        )
        key_browse_btn = MDRaisedButton(
            text="Browse",
            size_hint_x=0.3,
            on_press=lambda: self.browse_certificate('key')
        )
        key_layout.add_widget(self.config_key_file)
        key_layout.add_widget(key_browse_btn)
        form_layout.add_widget(key_layout)
        
        # Status Label
        self.config_status = MDLabel(
            text="Status: Disconnected ❌",
            halign="center",
            size_hint_y=None,
            height=40,
            markup=True
        )
        form_layout.add_widget(self.config_status)
        
        scroll.add_widget(form_layout)
        main_layout.add_widget(scroll)
        
        # Button Layout
        button_layout = MDBoxLayout(size_hint_y=None, height=60, spacing=10, padding=10)
        
        connect_btn = MDRaisedButton(
            text="Connect",
            size_hint_x=0.33,
            on_press=self.connect_mqtt
        )
        disconnect_btn = MDRaisedButton(
            text="Disconnect",
            size_hint_x=0.33,
            on_press=self.disconnect_mqtt
        )
        next_btn = MDRaisedButton(
            text="Next →",
            size_hint_x=0.34,
            disabled=True
        )
        self.config_next_btn = next_btn
        next_btn.on_press = self.go_to_fpi_screen
        
        button_layout.add_widget(connect_btn)
        button_layout.add_widget(disconnect_btn)
        button_layout.add_widget(next_btn)
        
        main_layout.add_widget(button_layout)
        config_screen.add_widget(main_layout)

    def build_fpi_screen(self, fpi_screen):
        """Build the FPI Login/Operations Screen"""
        fpi_screen.clear_widgets()
        
        main_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Title
        title = MDLabel(text="[b]FPI - MQTT Operations[/b]", markup=True, size_hint_y=None, height=40)
        main_layout.add_widget(title)
        
        # Scrollable area
        scroll = MDScrollView(size_hint=(1, 0.85))
        form_layout = MDGridLayout(cols=1, spacing=15, size_hint_y=None, padding=10)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # IMEI Number
        self.fpi_imei = MDTextField(
            hint_text="Enter IMEI No",
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.fpi_imei)
        
        # Subscribe Topics Label
        sub_label = MDLabel(
            text="[b]Topics to Subscribe:[/b]",
            markup=True,
            size_hint_y=None,
            height=30
        )
        form_layout.add_widget(sub_label)
        
        self.fpi_sub_topics = MDLabel(
            text="",
            markup=True,
            size_hint_y=None,
            height=60
        )
        form_layout.add_widget(self.fpi_sub_topics)
        
        # Publish Topic Label
        pub_label = MDLabel(
            text="[b]Topic to Publish:[/b]",
            markup=True,
            size_hint_y=None,
            height=30
        )
        form_layout.add_widget(pub_label)
        
        self.fpi_pub_topic = MDLabel(
            text="",
            size_hint_y=None,
            height=30
        )
        form_layout.add_widget(self.fpi_pub_topic)
        
        # JSON Payload
        self.fpi_payload = MDTextField(
            hint_text='Enter JSON Payload (e.g. {"cmd": "write", "3499": 1})',
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=80,
            multiline=True
        )
        form_layout.add_widget(self.fpi_payload)
        
        # Publish Button
        pub_btn = MDRaisedButton(
            text="Publish",
            size_hint_x=1,
            size_hint_y=None,
            height=45,
            on_press=self.publish_message
        )
        form_layout.add_widget(pub_btn)
        
        # Messages Display Label
        msg_label = MDLabel(
            text="[b]Received Messages:[/b]",
            markup=True,
            size_hint_y=None,
            height=30
        )
        form_layout.add_widget(msg_label)
        
        # Messages ScrollView
        msg_scroll = MDScrollView(size_hint_y=None, height=150)
        self.fpi_messages = MDLabel(
            text="",
            markup=True,
            size_hint_y=None,
            text_size=(400, None)
        )
        self.fpi_messages.bind(texture_size=self.fpi_messages.setter('size'))
        msg_scroll.add_widget(self.fpi_messages)
        form_layout.add_widget(msg_scroll)
        
        scroll.add_widget(form_layout)
        main_layout.add_widget(scroll)
        
        # Button Layout
        button_layout = MDBoxLayout(size_hint_y=None, height=60, spacing=10)
        
        back_btn = MDRaisedButton(
            text="← Back",
            size_hint_x=0.5,
            on_press=self.go_to_config_screen
        )
        clear_btn = MDRaisedButton(
            text="Clear Messages",
            size_hint_x=0.5,
            on_press=self.clear_messages
        )
        
        button_layout.add_widget(back_btn)
        button_layout.add_widget(clear_btn)
        
        main_layout.add_widget(button_layout)
        fpi_screen.add_widget(main_layout)

    def browse_certificate(self, cert_type):
        """Browse certificate file - allows manual entry"""
        self.config_status.text = f"📝 Please paste the {cert_type.upper()} certificate path in the field above"

    def connect_mqtt(self, instance=None):
        """Connect to MQTT Broker"""
        project_url = self.config_project_url.text.strip()
        username = self.config_username.text.strip()
        password = self.config_password.text.strip()
        
        if not project_url or not username or not password:
            self.config_status.text = "Status: ⚠️ Please fill all fields"
            return
        
        # Get certificate paths from text fields or internal variables
        ca_cert = self.config_ca_cert.text.strip() or self.ca_cert
        client_cert = self.config_client_cert.text.strip() or self.client_cert
        key_file = self.config_key_file.text.strip() or self.key_file
        
        if not ca_cert or not client_cert or not key_file:
            self.config_status.text = "Status: ⚠️ Please select/enter all certificates"
            return
        
        # Verify certificate files exist
        for cert_name, cert_path in [("CA Cert", ca_cert), ("Client Cert", client_cert), ("Key File", key_file)]:
            if not os.path.exists(cert_path):
                self.config_status.text = f"Status: ❌ {cert_name} not found: {cert_path}"
                return
        
        try:
            self.config_status.text = "Status: 🔄 Connecting..."
            
            self.client = mqtt.Client(
                client_id="FPI_APP_CLIENT",
                clean_session=True,
                protocol=mqtt.MQTTv311
            )
            
            # TLS Configuration
            self.client.tls_set(
                ca_certs=ca_cert,
                certfile=client_cert,
                keyfile=key_file,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
            )
            self.client.tls_insecure_set(False)
            
            # Authentication
            self.client.username_pw_set(username, password)
            
            # Callbacks
            self.client.on_connect = self.on_mqtt_connect
            self.client.on_disconnect = self.on_mqtt_disconnect
            self.client.on_message = self.on_mqtt_message
            
            # Connection
            self.client.connect(project_url, PORT, keepalive=KEEP_ALIVE)
            self.client.loop_start()
            
        except Exception as e:
            self.config_status.text = f"Status: ❌ Error: {str(e)}"
            print(f"Connection Error: {e}")

    def disconnect_mqtt(self, instance=None):
        """Disconnect from MQTT Broker"""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            self.is_connected = False
            self.config_next_btn.disabled = True
            self.config_status.text = "Status: Disconnected ❌"

    @mainthread
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.config_status.text = "Status: Connected ✅"
            self.is_connected = True
            self.config_next_btn.disabled = False
            print("✅ MQTT Connected successfully")
        else:
            self.config_status.text = f"Status: Connection Failed ❌ (Code {rc})"
            self.is_connected = False
            print(f"❌ Connection failed with code {rc}")

    @mainthread
    def on_mqtt_disconnect(self, client, userdata, rc):
        self.config_status.text = "Status: Disconnected ❌"
        self.is_connected = False
        self.config_next_btn.disabled = True
        print(f"❌ Disconnected with code {rc}")

    @mainthread
    def on_mqtt_message(self, client, userdata, msg):
        """Handle received messages"""
        message = f"📨 {msg.topic}: {msg.payload.decode()}\n"
        self.fpi_messages.text = message + self.fpi_messages.text
        print(f"Message: {msg.topic} - {msg.payload.decode()}")

    def go_to_fpi_screen(self, instance=None):
        """Navigate to FPI Screen"""
        if self.is_connected:
            self.screen_manager.current = 'fpi'
            self.fpi_imei.focus = True

    def go_to_config_screen(self, instance=None):
        """Navigate back to Config Screen"""
        self.screen_manager.current = 'config'

    def update_fpi_topics(self, imei):
        """Update topics based on IMEI"""
        if imei:
            publish_topic = f"iiot-1/substation/{imei}/ondemand/sub"
            subscribe_topics = f"iiot-1/substation/{imei}/+/+\niiot-1/substation/{imei}/otp/sub"
            
            self.fpi_pub_topic.text = publish_topic
            self.fpi_sub_topics.text = subscribe_topics

    def publish_message(self, instance=None):
        """Publish message to MQTT topic"""
        imei = self.fpi_imei.text.strip()
        payload = self.fpi_payload.text.strip()
        
        if not imei:
            self.fpi_messages.text = "❌ Please enter IMEI No\n" + self.fpi_messages.text
            return
        
        if not payload:
            self.fpi_messages.text = "❌ Please enter JSON payload\n" + self.fpi_messages.text
            return
        
        # Update topics
        self.update_fpi_topics(imei)
        
        # Subscribe to topics
        sub_topics = [
            f"iiot-1/substation/{imei}/+/+",
            f"iiot-1/substation/{imei}/otp/sub"
        ]
        
        for topic in sub_topics:
            self.client.subscribe(topic)
        
        # Publish message
        pub_topic = f"iiot-1/substation/{imei}/ondemand/sub"
        
        try:
            # Validate JSON
            json.loads(payload)
            self.client.publish(pub_topic, payload)
            self.fpi_messages.text = f"✅ Published to {pub_topic}\n" + self.fpi_messages.text
            print(f"✅ Published: {pub_topic} - {payload}")
        except json.JSONDecodeError:
            self.fpi_messages.text = "❌ Invalid JSON format\n" + self.fpi_messages.text
        except Exception as e:
            self.fpi_messages.text = f"❌ Error: {str(e)}\n" + self.fpi_messages.text

    def clear_messages(self, instance=None):
        """Clear received messages"""
        self.fpi_messages.text = ""

if __name__ == "__main__":
    MainApp().run()
