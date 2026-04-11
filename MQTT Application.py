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
from kivy.graphics import Color, RoundedRectangle
import paho.mqtt.client as mqtt
import ssl
import socket
import os
import json
import threading
import subprocess

# =========================
# MQTT CONFIG
# =========================
PORT = 8883  # TLS Port
KEEP_ALIVE = 60  # seconds (increased from 10)
RECONNECT_DELAY = 1  # seconds
CONNECT_TIMEOUT = 5  # Connection timeout in seconds

# Default Credentials
DEFAULT_USERNAME = "hkrpadmin"
DEFAULT_PASSWORD = "hkrpadmin@2021"

# Project URL Mapping (Dynamic Dictionary)
PROJECT_URLS = {
    "UGVCL RDSS": "fepugvcl.scada-rdss.com",
    "SFMS": "dbrokersfms.hkapl.in",
    # Add more projects here easily
}

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
    selected_project = None
    selected_url = None

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
        
        # Project Selection Dropdown
        project_label = MDLabel(
            text="[b]Select Project:[/b]",
            markup=True,
            size_hint_y=None,
            height=25,
            font_size="12sp"
        )
        form_layout.add_widget(project_label)
        
        # Create dropdown items from PROJECT_URLS dictionary with callbacks
        dropdown_items = []
        for project_name in PROJECT_URLS.keys():
            dropdown_items.append({
                "text": project_name,
                "on_release": lambda name=project_name: self.on_project_selected(name)
            })
        # Add "Other" option for manual entry
        dropdown_items.append({
            "text": "Other (Manual Entry)",
            "on_release": lambda: self.on_project_selected("Other (Manual Entry)")
        })
        
        self.config_project_dropdown = MDRaisedButton(
            text="Select Project",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_project_dropdown)
        
        # Dropdown menu
        self.project_menu = MDDropdownMenu(
            caller=self.config_project_dropdown,
            items=dropdown_items,
            width_mult=4,
        )
        self.config_project_dropdown.bind(on_press=lambda instance: self.project_menu.open())
        
        # Manual URL entry field (visible only when "Other" is selected)
        self.config_project_url = MDTextField(
            hint_text="Enter Project URL manually",
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        self.config_project_url.opacity = 0
        self.config_project_url.disabled = True
        form_layout.add_widget(self.config_project_url)
        
        # Username with default value
        self.config_username = MDTextField(
            hint_text="Username",
            text=DEFAULT_USERNAME,
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_username)
        
        # Password with default value
        self.config_password = MDTextField(
            hint_text="Password",
            text=DEFAULT_PASSWORD,
            password=True,
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=45
        )
        form_layout.add_widget(self.config_password)
        
        # Status Label with enhanced styling
        self.config_status = MDLabel(
            text="[b]● Disconnected[/b]",
            halign="center",
            valign="center",
            size_hint_y=None,
            height=80,
            markup=True,
            font_size="22sp",
            bold=True,
            color=(1, 0.3, 0.3, 1),  # Bright red
            padding=(10, 10),
            line_height=1.5
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
        
        # IMEI Input Section
        imei_layout = MDBoxLayout(size_hint_y=None, height=60, spacing=10)
        self.fpi_imei = MDTextField(
            hint_text="Enter IMEI No",
            mode="rectangle",
            size_hint_x=0.7
        )
        go_btn = MDRaisedButton(
            text="Go",
            size_hint_x=0.3,
            on_press=self.on_imei_go_clicked
        )
        imei_layout.add_widget(self.fpi_imei)
        imei_layout.add_widget(go_btn)
        main_layout.add_widget(imei_layout)
        
        # Scrollable area for topics
        scroll = MDScrollView(size_hint=(1, 0.85))
        form_layout = MDGridLayout(cols=1, spacing=12, size_hint_y=None, padding=8)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        # ========== SECTION 1: Topic 1 Subscription ==========
        topic1_header = MDBoxLayout(size_hint_y=None, height=45, padding=10)
        
        def update_topic1_canvas(*args):
            topic1_header.canvas.before.clear()
            with topic1_header.canvas.before:
                Color(0.1, 0.5, 0.8, 1)  # Blue
                RoundedRectangle(size=topic1_header.size, pos=topic1_header.pos, radius=[10])
        
        topic1_header.bind(pos=update_topic1_canvas, size=update_topic1_canvas)
        update_topic1_canvas()
        
        self.fpi_topic1_label = MDLabel(
            text="[b]📨 Topic 1: iiot-1/substation/[IMEI]/+/+[/b]",
            markup=True,
            font_size="14sp",
            bold=True,
            color=(1, 1, 1, 1)
        )
        topic1_header.add_widget(self.fpi_topic1_label)
        form_layout.add_widget(topic1_header)
        
        # Message display with colored background
        topic1_msg_container = MDBoxLayout(size_hint_y=None, height=160, padding=2)
        def update_topic1_msg_bg(*args):
            topic1_msg_container.canvas.before.clear()
            with topic1_msg_container.canvas.before:
                Color(0.1, 0.5, 0.8, 0.15)  # Light blue background
                RoundedRectangle(size=topic1_msg_container.size, pos=topic1_msg_container.pos, radius=[8])
        topic1_msg_container.bind(pos=update_topic1_msg_bg, size=update_topic1_msg_bg)
        update_topic1_msg_bg()
        
        self.fpi_topic1_messages = MDLabel(
            text="[i]Waiting for messages...[/i]",
            markup=True,
            size_hint_y=None,
            height=100,
            text_size=(700, None),
            font_size="12sp",
            padding=(8, 8)
        )
        self.fpi_topic1_messages.bind(texture_size=self.fpi_topic1_messages.setter('size'))
        
        topic1_scroll = MDScrollView(size_hint_y=None, height=160)
        topic1_scroll.add_widget(self.fpi_topic1_messages)
        topic1_msg_container.add_widget(topic1_scroll)
        form_layout.add_widget(topic1_msg_container)
        
        # ========== SECTION 2: Topic 2 Subscription ==========
        topic2_header = MDBoxLayout(size_hint_y=None, height=45, padding=10)
        
        def update_topic2_canvas(*args):
            topic2_header.canvas.before.clear()
            with topic2_header.canvas.before:
                Color(0.8, 0.4, 0.1, 1)  # Orange
                RoundedRectangle(size=topic2_header.size, pos=topic2_header.pos, radius=[10])
        
        topic2_header.bind(pos=update_topic2_canvas, size=update_topic2_canvas)
        update_topic2_canvas()
        
        self.fpi_topic2_label = MDLabel(
            text="[b]🔐 Topic 2: iiot-1/substation/[IMEI]/otp/sub[/b]",
            markup=True,
            font_size="14sp",
            bold=True,
            color=(1, 1, 1, 1)
        )
        topic2_header.add_widget(self.fpi_topic2_label)
        form_layout.add_widget(topic2_header)
        
        # Message display with colored background
        topic2_msg_container = MDBoxLayout(size_hint_y=None, height=160, padding=2)
        def update_topic2_msg_bg(*args):
            topic2_msg_container.canvas.before.clear()
            with topic2_msg_container.canvas.before:
                Color(0.8, 0.4, 0.1, 0.15)  # Light orange background
                RoundedRectangle(size=topic2_msg_container.size, pos=topic2_msg_container.pos, radius=[8])
        topic2_msg_container.bind(pos=update_topic2_msg_bg, size=update_topic2_msg_bg)
        update_topic2_msg_bg()
        
        self.fpi_topic2_messages = MDLabel(
            text="[i]Waiting for messages...[/i]",
            markup=True,
            size_hint_y=None,
            height=100,
            text_size=(700, None),
            font_size="12sp",
            padding=(8, 8)
        )
        self.fpi_topic2_messages.bind(texture_size=self.fpi_topic2_messages.setter('size'))
        
        topic2_scroll = MDScrollView(size_hint_y=None, height=160)
        topic2_scroll.add_widget(self.fpi_topic2_messages)
        topic2_msg_container.add_widget(topic2_scroll)
        form_layout.add_widget(topic2_msg_container)
        
        # ========== SECTION 3: Topic 3 Publishing ==========
        topic3_header = MDBoxLayout(size_hint_y=None, height=45, padding=10)
        
        def update_topic3_canvas(*args):
            topic3_header.canvas.before.clear()
            with topic3_header.canvas.before:
                Color(0.2, 0.7, 0.2, 1)  # Green
                RoundedRectangle(size=topic3_header.size, pos=topic3_header.pos, radius=[10])
        
        topic3_header.bind(pos=update_topic3_canvas, size=update_topic3_canvas)
        update_topic3_canvas()
        
        self.fpi_topic3_label = MDLabel(
            text="[b]📤 Topic 3: iiot-1/substation/[IMEI]/ondemand/sub[/b]",
            markup=True,
            font_size="14sp",
            bold=True,
            color=(1, 1, 1, 1)
        )
        topic3_header.add_widget(self.fpi_topic3_label)
        form_layout.add_widget(topic3_header)
        
        # JSON Payload
        self.fpi_payload = MDTextField(
            hint_text='JSON Payload (e.g. {"cmd": "write", "3499": 1})',
            mode="rectangle",
            size_hint_x=1,
            size_hint_y=None,
            height=100,
            multiline=True
        )
        form_layout.add_widget(self.fpi_payload)
        
        # Publish Button
        pub_btn = MDRaisedButton(
            text="Publish",
            size_hint_x=1,
            size_hint_y=None,
            height=50,
            on_press=self.publish_message
        )
        form_layout.add_widget(pub_btn)
        
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

    @mainthread
    def on_project_selected(self, project_name):
        """Handle project dropdown selection"""
        if self.project_menu:
            self.project_menu.dismiss()
        
        if project_name == "Other (Manual Entry)":
            # Show manual URL entry field
            self.config_project_url.opacity = 1
            self.config_project_url.disabled = False
            self.selected_project = "Other"
            self.selected_url = None
            self.config_project_dropdown.text = "Other (Manual Entry)"
            print("[DEBUG] Selected: Other - Manual URL entry enabled")
        else:
            # Get URL from dictionary
            self.selected_project = project_name
            self.selected_url = PROJECT_URLS.get(project_name)
            self.config_project_url.opacity = 0
            self.config_project_url.disabled = True
            self.config_project_url.text = ""
            self.config_project_dropdown.text = project_name
            print(f"[DEBUG] Selected: {project_name} - URL: {self.selected_url}")

    def connect_mqtt(self, instance=None):
        """Connect to MQTT Broker using Username and Password (TLS)"""
        # Get URL from either selected project or manual entry
        if self.selected_project == "Other":
            project_url = self.config_project_url.text.strip()
        else:
            project_url = self.selected_url
        
        username = self.config_username.text.strip()
        password = self.config_password.text.strip()
        
        if not project_url or not username or not password:
            self.config_status.text = "[b]● Error[/b]\n[size=16sp]Please select project & fill credentials[/size]"
            self.config_status.color = (1, 0.3, 0.3, 1)
            return
        
        def connect_in_thread():
            try:
                print(f"[DEBUG] Attempting connection to {project_url}:{PORT}")
                self.client = mqtt.Client(
                    client_id="FPI_APP_CLIENT",
                    clean_session=True,
                    protocol=mqtt.MQTTv311
                )
                
                self.client._connect_timeout = CONNECT_TIMEOUT
                self.client._sock_connect_timeout = CONNECT_TIMEOUT
                
                self.client.tls_set(
                    ca_certs=None,
                    certfile=None,
                    keyfile=None,
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLS
                )
                self.client.tls_insecure_set(True)
                
                self.client.username_pw_set(username, password)
                
                self.client.on_connect = self.on_mqtt_connect
                self.client.on_disconnect = self.on_mqtt_disconnect
                self.client.on_message = self.on_mqtt_message
                self.client.on_socket_connect = self.on_socket_connect
                self.client.on_socket_close = self.on_socket_close
                
                print(f"[DEBUG] Starting TLS connection to {project_url}:{PORT}...")
                self.client.connect(project_url, PORT, keepalive=KEEP_ALIVE)
                print(f"[DEBUG] Connection successful, starting loop...")
                self.client.loop_start()
                
            except socket.timeout:
                print("[ERROR] Connection timeout - broker not responding")
                self.config_status.text = "[b]● Connection Failed[/b]\n[size=14sp]Timeout: Broker not responding[/size]"
                self.config_status.color = (1, 0.3, 0.3, 1)
            except socket.gaierror:
                print(f"[ERROR] Name resolution failed - invalid broker address")
                self.config_status.text = "[b]● Connection Failed[/b]\n[size=14sp]Invalid broker address[/size]"
                self.config_status.color = (1, 0.3, 0.3, 1)
            except ConnectionRefusedError:
                print("[ERROR] Connection refused - broker not listening")
                self.config_status.text = "[b]● Connection Failed[/b]\n[size=14sp]Port not open/Broker offline[/size]"
                self.config_status.color = (1, 0.3, 0.3, 1)
            except Exception as e:
                print(f"[ERROR] Connection error: {type(e).__name__}: {e}")
                self.config_status.text = f"[b]● Error[/b]\n[size=14sp]{str(e)[:40]}[/size]"
                self.config_status.color = (1, 0.3, 0.3, 1)
        
        self.config_status.text = "[b]● Connecting[/b]\n[size=16sp]Establishing connection...[/size]"
        self.config_status.color = (1, 0.8, 0, 1)
        
        threading.Thread(target=connect_in_thread, daemon=True).start()

    def disconnect_mqtt(self, instance=None):
        """Disconnect from MQTT Broker"""
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
            self.is_connected = False
            self.config_next_btn.disabled = True
            self.config_status.text = "[b]Disconnected ❌[/b]"

    def on_socket_connect(self, client, userdata, sock):
        """Called when socket is opened"""
        print("[DEBUG] 📡 Socket connected to broker")

    def on_socket_close(self, client, userdata, sock):
        """Called when socket is closed"""
        print("[DEBUG] ❌ Socket closed")

    def on_socket_open(self, client, userdata, sock):
        """Called when socket connection is established"""
        print("[DEBUG] 🔌 Socket opened - awaiting MQTT handshake")

    @mainthread
    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.config_status.text = "[b]● Connected Successfully[/b]\n[size=16sp]Ready to publish messages[/size]"
            self.config_status.color = (0.1, 0.8, 0.1, 1)  # Bright green
            self.is_connected = True
            self.config_next_btn.disabled = False
            print("✅ MQTT Connected successfully")
        else:
            # MQTT error code mapping
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code {rc}")
            self.config_status.text = f"[b]● Connection Failed[/b]\n[size=14sp]{error_msg}[/size]"
            self.config_status.color = (1, 0.3, 0.3, 1)  # Bright red
            self.is_connected = False
            print(f"❌ Connection failed: {error_msg}")

    @mainthread
    def on_mqtt_disconnect(self, client, userdata, rc):
        self.config_status.text = "[b]● Disconnected[/b]\n[size=16sp]Not connected to broker[/size]"
        self.config_status.color = (1, 0.3, 0.3, 1)  # Bright red
        self.is_connected = False
        self.config_next_btn.disabled = True
        print(f"❌ Disconnected with code {rc}")

    @mainthread
    def on_mqtt_message(self, client, userdata, msg):
        """Handle received messages - route to correct topic display"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Decode message payload
        try:
            payload = msg.payload.decode('utf-8')
        except:
            payload = str(msg.payload)
        
        # Format message with timestamp
        message_text = f"[{timestamp}] {payload}"
        
        print(f"[DEBUG] Message received on topic: {msg.topic}")
        print(f"[DEBUG] Current IMEI: {self.current_imei}")
        
        # Route to correct section based on topic
        # Topic 1: iiot-1/substation/{IMEI}/+/+ (any message matching IMEI but NOT otp/sub)
        # Topic 2: iiot-1/substation/{IMEI}/otp/sub
        
        if self.current_imei and self.current_imei in msg.topic:
            if "/otp/sub" in msg.topic:  # Topic 2
                self.fpi_topic2_messages.text = message_text + "\n" + self.fpi_topic2_messages.text
                print(f"[✅ Topic 2] {msg.topic}: {payload}")
            else:  # Topic 1 (contains IMEI but NOT otp/sub)
                self.fpi_topic1_messages.text = message_text + "\n" + self.fpi_topic1_messages.text
                print(f"[✅ Topic 1] {msg.topic}: {payload}")
        else:
            print(f"[OTHER] {msg.topic}: {payload}")

    def on_imei_go_clicked(self, instance=None):
        """Handle IMEI Go button click - subscribe to topics and setup"""
        imei = self.fpi_imei.text.strip()
        
        if not imei:
            return
        
        if not self.is_connected:
            return
        
        # Store IMEI for later use
        self.current_imei = imei
        
        # Subscribe to both topics
        topic1 = f"iiot-1/substation/{imei}/+/+"
        topic2 = f"iiot-1/substation/{imei}/otp/sub"
        topic3 = f"iiot-1/substation/{imei}/ondemand/sub"
        
        self.client.subscribe(topic1)
        self.client.subscribe(topic2)
        
        # Update topic labels with actual IMEI
        self.fpi_topic1_label.text = f"[b]Topic 1: {topic1}[/b]"
        self.fpi_topic2_label.text = f"[b]Topic 2: {topic2}[/b]"
        self.fpi_topic3_label.text = f"[b]Topic 3: {topic3}[/b]"
        
        # Clear previous messages
        self.fpi_topic1_messages.text = "[i]Subscribed - Waiting for messages...[/i]"
        self.fpi_topic2_messages.text = "[i]Subscribed - Waiting for messages...[/i]"
        
        print(f"✅ Subscribed to topics for IMEI: {imei}")

    def go_to_fpi_screen(self, instance=None):
        """Navigate to FPI Screen"""
        if self.is_connected:
            self.screen_manager.current = 'fpi'
            self.fpi_imei.focus = True

    def go_to_config_screen(self, instance=None):
        """Navigate back to Config Screen"""
        # Unsubscribe from topics when going back
        if self.current_imei:
            topic1 = f"iiot-1/substation/{self.current_imei}/+/+"
            topic2 = f"iiot-1/substation/{self.current_imei}/otp/sub"
            self.client.unsubscribe(topic1)
            self.client.unsubscribe(topic2)
        
        self.screen_manager.current = 'config'

    def publish_message(self, instance=None):
        """Publish message to Topic 3"""
        imei = self.current_imei or self.fpi_imei.text.strip()
        payload = self.fpi_payload.text.strip()
        
        if not imei:
            return
        
        if not payload:
            return
        
        # Publish message to Topic 3
        pub_topic = f"iiot-1/substation/{imei}/ondemand/sub"
        
        try:
            # Validate JSON
            json.loads(payload)
            self.client.publish(pub_topic, payload)
            print(f"✅ Published to {pub_topic}: {payload}")
        except json.JSONDecodeError:
            print("❌ Invalid JSON format")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def clear_messages(self, instance=None):
        """Clear all received messages from three topic displays"""
        self.fpi_topic1_messages.text = "[i]Waiting for messages...[/i]"
        self.fpi_topic2_messages.text = "[i]Waiting for messages...[/i]"
        self.fpi_payload.text = ""

if __name__ == "__main__":
    MainApp().run()