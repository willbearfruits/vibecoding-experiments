import sys
import os
import json
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QListWidget, QListWidgetItem,
                            QTabWidget, QTextEdit, QSplitter, QFrame, QMessageBox, QToolBar,
                            QAction, QFileDialog, QScrollArea, QMenu, QInputDialog, QLineEdit)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon, QDrag, QPixmap, QPainterPath
from PyQt5.QtCore import Qt, QMimeData, QPoint, QRect, QSize, pyqtSignal, QTimer, QThread, QByteArray

class Pin:
    def __init__(self, id, name, x, y, pin_type):
        self.id = id
        self.name = name
        self.x = x
        self.y = y
        self.type = pin_type  # digital, analog, power, ground
        self.connected_to = None

class Component:
    def __init__(self, id, type_name, x, y, width, height):
        self.id = id
        self.type_name = type_name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pins = []

class Board:
    def __init__(self, name, width, height, pins):
        self.name = name
        self.width = width
        self.height = height
        self.pins = pins

class Connection:
    def __init__(self, id, source_pin, target_pin):
        self.id = id
        self.source_pin = source_pin
        self.target_pin = target_pin

class SerialMonitor(QThread):
    data_received = pyqtSignal(str)
    
    def __init__(self, port, baud_rate):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.running = False
        self.serial_port = None
    
    def run(self):
        try:
            self.serial_port = serial.Serial(self.port, self.baud_rate, timeout=0.1)
            self.running = True
            
            while self.running:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                    if data:
                        self.data_received.emit(data)
        except Exception as e:
            self.data_received.emit(f"Error: {str(e)}")
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
    
    def stop(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

class BoardDefinitions:
    @staticmethod
    def get_arduino_uno():
        pins = [
            Pin("D0", "0 (RX)", 270, 50, "digital"),
            Pin("D1", "1 (TX)", 270, 65, "digital"),
            Pin("D2", "2", 270, 80, "digital"),
            Pin("D3", "3 (PWM)", 270, 95, "digital"),
            Pin("D4", "4", 270, 110, "digital"),
            Pin("D5", "5 (PWM)", 270, 125, "digital"),
            Pin("D6", "6 (PWM)", 270, 140, "digital"),
            Pin("D7", "7", 270, 155, "digital"),
            Pin("D8", "8", 270, 170, "digital"),
            Pin("D9", "9 (PWM)", 270, 185, "digital"),
            Pin("D10", "10 (PWM)", 240, 185, "digital"),
            Pin("D11", "11 (PWM)", 210, 185, "digital"),
            Pin("D12", "12", 180, 185, "digital"),
            Pin("D13", "13 (LED)", 150, 185, "digital"),
            Pin("A0", "A0", 120, 185, "analog"),
            Pin("A1", "A1", 90, 185, "analog"),
            Pin("A2", "A2", 60, 185, "analog"),
            Pin("A3", "A3", 30, 185, "analog"),
            Pin("A4", "A4 (SDA)", 30, 155, "analog"),
            Pin("A5", "A5 (SCL)", 30, 125, "analog"),
            Pin("GND1", "GND", 30, 95, "power"),
            Pin("RESET", "RESET", 30, 65, "control"),
            Pin("3V3", "3.3V", 30, 50, "power"),
            Pin("5V", "5V", 60, 50, "power"),
            Pin("GND2", "GND", 90, 50, "power"),
        ]
        return Board("Arduino Uno", 300, 200, pins)
    
    @staticmethod
    def get_esp32():
        pins = [
            Pin("D0", "GPIO0", 270, 40, "digital"),
            Pin("D1", "GPIO1", 270, 55, "digital"),
            Pin("D2", "GPIO2", 270, 70, "digital"),
            Pin("D3", "GPIO3", 270, 85, "digital"),
            Pin("D4", "GPIO4", 270, 100, "digital"),
            Pin("D5", "GPIO5", 270, 115, "digital"),
            Pin("D12", "GPIO12", 270, 130, "digital"),
            Pin("D13", "GPIO13", 270, 145, "digital"),
            Pin("D14", "GPIO14", 270, 160, "digital"),
            Pin("D15", "GPIO15", 270, 175, "digital"),
            Pin("D16", "GPIO16", 250, 175, "digital"),
            Pin("D17", "GPIO17", 230, 175, "digital"),
            Pin("D18", "GPIO18", 210, 175, "digital"),
            Pin("D19", "GPIO19", 190, 175, "digital"),
            Pin("D21", "GPIO21", 170, 175, "digital"),
            Pin("D22", "GPIO22", 150, 175, "digital"),
            Pin("D23", "GPIO23", 130, 175, "digital"),
            Pin("D25", "GPIO25", 110, 175, "digital"),
            Pin("D26", "GPIO26", 90, 175, "digital"),
            Pin("D27", "GPIO27", 70, 175, "digital"),
            Pin("D32", "GPIO32", 50, 175, "digital"),
            Pin("D33", "GPIO33", 30, 175, "digital"),
            Pin("D34", "GPIO34", 30, 155, "analog"),
            Pin("D35", "GPIO35", 30, 135, "analog"),
            Pin("D36", "GPIO36", 30, 115, "analog"),
            Pin("D39", "GPIO39", 30, 95, "analog"),
            Pin("GND", "GND", 30, 75, "power"),
            Pin("VIN", "VIN", 30, 55, "power"),
            Pin("3V3", "3.3V", 30, 35, "power"),
        ]
        return Board("ESP32", 300, 200, pins)
    
    @staticmethod
    def get_teensy():
        pins = [
            Pin("GND1", "GND", 30, 30, "power"),
            Pin("D0", "0", 50, 30, "digital"),
            Pin("D1", "1", 70, 30, "digital"),
            Pin("D2", "2", 90, 30, "digital"),
            Pin("D3", "3", 110, 30, "digital"),
            Pin("D4", "4", 130, 30, "digital"),
            Pin("D5", "5", 150, 30, "digital"),
            Pin("D6", "6", 170, 30, "digital"),
            Pin("D7", "7", 190, 30, "digital"),
            Pin("D8", "8", 210, 30, "digital"),
            Pin("D9", "9", 230, 30, "digital"),
            Pin("D10", "10", 250, 30, "digital"),
            Pin("D11", "11", 250, 50, "digital"),
            Pin("D12", "12", 250, 70, "digital"),
            Pin("D13", "13", 250, 90, "digital"),
            Pin("D14", "14/A0", 250, 110, "digital"),
            Pin("D15", "15/A1", 230, 110, "digital"),
            Pin("D16", "16/A2", 210, 110, "digital"),
            Pin("D17", "17/A3", 190, 110, "digital"),
            Pin("D18", "18/A4", 170, 110, "digital"),
            Pin("D19", "19/A5", 150, 110, "digital"),
            Pin("D20", "20/A6", 130, 110, "digital"),
            Pin("D21", "21/A7", 110, 110, "digital"),
            Pin("D22", "22/A8", 90, 110, "digital"),
            Pin("D23", "23/A9", 70, 110, "digital"),
            Pin("3V3", "3.3V", 50, 110, "power"),
            Pin("GND2", "GND", 30, 110, "power"),
        ]
        return Board("Teensy 4.0", 280, 150, pins)
    
    @staticmethod
    def get_daisy():
        pins = [
            Pin("3V3", "3.3V", 30, 30, "power"),
            Pin("GND1", "GND", 50, 30, "power"),
            Pin("D1", "D1", 70, 30, "digital"),
            Pin("D2", "D2", 90, 30, "digital"),
            Pin("D3", "D3", 110, 30, "digital"),
            Pin("D4", "D4", 130, 30, "digital"),
            Pin("D5", "D5", 150, 30, "digital"),
            Pin("D6", "D6", 170, 30, "digital"),
            Pin("D7", "D7", 190, 30, "digital"),
            Pin("D8", "D8", 210, 30, "digital"),
            Pin("D9", "D9", 230, 30, "digital"),
            Pin("D10", "D10", 230, 50, "digital"),
            Pin("D11", "D11", 230, 70, "digital"),
            Pin("D12", "D12", 230, 90, "digital"),
            Pin("D13", "D13", 230, 110, "digital"),
            Pin("D14", "D14", 230, 130, "digital"),
            Pin("D15", "D15", 210, 130, "digital"),
            Pin("A0", "A0", 190, 130, "analog"),
            Pin("A1", "A1", 170, 130, "analog"),
            Pin("A2", "A2", 150, 130, "analog"),
            Pin("A3", "A3", 130, 130, "analog"),
            Pin("A4", "A4", 110, 130, "analog"),
            Pin("A5", "A5", 90, 130, "analog"),
            Pin("A6", "A6", 70, 130, "analog"),
            Pin("A7", "A7", 50, 130, "analog"),
            Pin("GND2", "GND", 30, 130, "power"),
        ]
        return Board("Daisy Seed", 250, 170, pins)
    
    @staticmethod
    def get_board(board_type):
        if board_type == "arduino":
            return BoardDefinitions.get_arduino_uno()
        elif board_type == "esp32":
            return BoardDefinitions.get_esp32()
        elif board_type == "teensy":
            return BoardDefinitions.get_teensy()
        elif board_type == "daisy":
            return BoardDefinitions.get_daisy()
        else:
            return BoardDefinitions.get_arduino_uno()

class ComponentDefinitions:
    @staticmethod
    def get_component_types():
        return [
            {
                "id": "led",
                "name": "LED",
                "icon": "💡",
                "color": "#FF5252",
                "pins": [
                    {"name": "power", "type": "input"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "button",
                "name": "Button",
                "icon": "🔘",
                "color": "#2196F3",
                "pins": [
                    {"name": "signal", "type": "output"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "pot",
                "name": "Potentiometer",
                "icon": "🎚️",
                "color": "#4CAF50",
                "pins": [
                    {"name": "signal", "type": "output"},
                    {"name": "power", "type": "input"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "servo",
                "name": "Servo Motor",
                "icon": "🔄",
                "color": "#9C27B0",
                "pins": [
                    {"name": "signal", "type": "input"},
                    {"name": "power", "type": "input"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "ultrasonic",
                "name": "Ultrasonic Sensor",
                "icon": "📡",
                "color": "#FFC107",
                "pins": [
                    {"name": "trigger", "type": "input"},
                    {"name": "echo", "type": "output"},
                    {"name": "power", "type": "input"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "rgb_led",
                "name": "RGB LED",
                "icon": "🌈",
                "color": "#E91E63",
                "pins": [
                    {"name": "red", "type": "input"},
                    {"name": "green", "type": "input"},
                    {"name": "blue", "type": "input"},
                    {"name": "ground", "type": "output"}
                ]
            },
            {
                "id": "custom",
                "name": "Custom Component",
                "icon": "⚙️",
                "color": "#607D8B",
                "pins": [
                    {"name": "pin1", "type": "input/output"},
                    {"name": "pin2", "type": "input/output"},
                    {"name": "pin3", "type": "input/output"},
                    {"name": "pin4", "type": "input/output"}
                ]
            }
        ]

class CodeGenerator:
    @staticmethod
    def generate_code_for_arduino(components, connections):
        code = "// Auto-generated code for Arduino\n\n"
        
        # Process each component and its connections
        for component in components:
            if component.type_name == "led":
                # Find LED pin connections
                power_pin = None
                for connection in connections:
                    if connection.target_pin.startswith(f"{component.id}_power"):
                        power_pin = connection.source_pin
                
                if power_pin:
                    code += f"#define LED_PIN {power_pin}\n\n"
                    code += "void setup() {\n"
                    code += f"  pinMode(LED_PIN, OUTPUT);\n"
                    code += "}\n\n"
                    code += "void loop() {\n"
                    code += "  digitalWrite(LED_PIN, HIGH);\n"
                    code += "  delay(1000);\n"
                    code += "  digitalWrite(LED_PIN, LOW);\n"
                    code += "  delay(1000);\n"
                    code += "}\n"
            
            elif component.type_name == "button":
                # Find button pin connections
                signal_pin = None
                for connection in connections:
                    if connection.target_pin.startswith(f"{component.id}_signal"):
                        signal_pin = connection.source_pin
                
                if signal_pin:
                    code += f"#define BUTTON_PIN {signal_pin}\n\n"
                    code += "void setup() {\n"
                    code += f"  pinMode(BUTTON_PIN, INPUT_PULLUP);\n"
                    code += "  Serial.begin(9600);\n"
                    code += "}\n\n"
                    code += "void loop() {\n"
                    code += "  if (digitalRead(BUTTON_PIN) == LOW) {\n"
                    code += "    Serial.println(\"Button pressed\");\n"
                    code += "  }\n"
                    code += "  delay(100);\n"
                    code += "}\n"
            
            # Add more component types as needed
        
        # If we have multiple components, create more complex code
        if len(components) > 1:
            component_definitions = []
            setup_lines = ["void setup() {", "  Serial.begin(9600);"]
            loop_lines = ["void loop() {"]
            
            for component in components:
                if component.type_name == "led":
                    for connection in connections:
                        if connection.target_pin.startswith(f"{component.id}_power"):
                            pin = connection.source_pin
                            component_definitions.append(f"#define LED_PIN_{component.id} {pin}")
                            setup_lines.append(f"  pinMode(LED_PIN_{component.id}, OUTPUT);")
                            loop_lines.append(f"  digitalWrite(LED_PIN_{component.id}, HIGH);")
                            loop_lines.append("  delay(500);")
                            loop_lines.append(f"  digitalWrite(LED_PIN_{component.id}, LOW);")
                            loop_lines.append("  delay(500);")
                
                elif component.type_name == "button":
                    for connection in connections:
                        if connection.target_pin.startswith(f"{component.id}_signal"):
                            pin = connection.source_pin
                            component_definitions.append(f"#define BUTTON_PIN_{component.id} {pin}")
                            setup_lines.append(f"  pinMode(BUTTON_PIN_{component.id}, INPUT_PULLUP);")
                            loop_lines.append(f"  if (digitalRead(BUTTON_PIN_{component.id}) == LOW) {{")
                            loop_lines.append(f"    Serial.println(\"{component.id} pressed\");")
                            loop_lines.append("  }")
            
            setup_lines.append("}")
            loop_lines.append("  delay(50);")
            loop_lines.append("}")
            
            # Combine all code sections
            if component_definitions:
                code = "// Auto-generated code for multiple components\n\n"
                code += "\n".join(component_definitions) + "\n\n"
                code += "\n".join(setup_lines) + "\n\n"
                code += "\n".join(loop_lines) + "\n"
        
        return code
    
    @staticmethod
    def generate_code_for_esp32(components, connections):
        # Similar to Arduino but with ESP32-specific code
        code = "// Auto-generated code for ESP32\n\n"
        # Add ESP32 specific code here
        return code
    
    @staticmethod
    def generate_code_for_teensy(components, connections):
        code = "// Auto-generated code for Teensy\n\n"
        # Add Teensy specific code here
        return code
    
    @staticmethod
    def generate_code_for_daisy(components, connections):
        code = "// Auto-generated code for Daisy\n\n"
        # Add Daisy specific code here
        return code
    
    @staticmethod
    def generate_code(board_type, components, connections):
        if board_type == "arduino":
            return CodeGenerator.generate_code_for_arduino(components, connections)
        elif board_type == "esp32":
            return CodeGenerator.generate_code_for_esp32(components, connections)
        elif board_type == "teensy":
            return CodeGenerator.generate_code_for_teensy(components, connections)
        elif board_type == "daisy":
            return CodeGenerator.generate_code_for_daisy(components, connections)
        else:
            return "// Unsupported board type\n"

class BoardCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        
        # Board properties
        self.board = None
        self.board_type = "arduino"
        self.change_board("arduino")
        
        # Component and connection management
        self.components = []
        self.connections = []
        self.next_component_id = 1
        self.next_connection_id = 1
        
        # Interaction states
        self.selected_component = None
        self.dragging_component = False
        self.drag_start_pos = QPoint()
        self.drag_offset = QPoint()
        
        self.drawing_connection = False
        self.connection_start_pin = None
        self.connection_end_pos = QPoint()
        self.hovered_pin = None
        
        # Colors and styles
        self.pin_colors = {
            "digital": QColor(76, 175, 80),  # Green
            "analog": QColor(33, 150, 243),  # Blue
            "power": QColor(255, 87, 34),    # Orange
            "control": QColor(158, 158, 158)  # Gray
        }
        
        self.setAcceptDrops(True)
    
    def change_board(self, board_type):
        self.board_type = board_type
        self.board = BoardDefinitions.get_board(board_type)
        self.components = []
        self.connections = []
        self.update()
    
    def add_component(self, component_type):
        component_types = ComponentDefinitions.get_component_types()
        comp_def = next((c for c in component_types if c["id"] == component_type), None)
        
        if comp_def:
            # Create component instance
            component = Component(
                f"{component_type}_{self.next_component_id}",
                component_type,
                400,  # Default X position
                150,  # Default Y position
                100,   # Default width
                80     # Default height
            )
            self.next_component_id += 1
            
            # Add pins to component
            for i, pin_def in enumerate(comp_def["pins"]):
                pin_id = f"{component.id}_{pin_def['name']}"
                # Pin positions will be calculated during rendering
                component.pins.append(Pin(pin_id, pin_def["name"], 0, 0, pin_def["type"]))
            
            self.components.append(component)
            self.update()
            return component
        
        return None
    
    def find_pin_at_position(self, pos):
        # Check board pins
        for pin in self.board.pins:
            pin_rect = QRect(int(pin.x) - 5, int(pin.y) - 5, 10, 10)
            if pin_rect.contains(pos):
                return pin, "board", None
        
        # Check component pins
        for component in self.components:
            # Calculate pin positions for this component
            for pin in component.pins:
                pin_pos = self.calculate_pin_position(pin, component)
                pin_rect = QRect(int(pin_pos[0]) - 5, int(pin_pos[1]) - 5, 10, 10)
                if pin_rect.contains(pos):
                    return pin, "component", component
        
        return None, None, None
    
    def calculate_pin_position(self, pin, component):
        # Calculate pin position based on component position and size
        pin_index = component.pins.index(pin)
        total_pins = len(component.pins)
        
        if total_pins == 1:
            return component.x + component.width / 2, component.y + component.height / 2
        elif total_pins == 2:
            if pin_index == 0:
                return component.x, component.y + component.height / 2
            else:
                return component.x + component.width, component.y + component.height / 2
        else:
            # Distribute pins around the component
            if pin_index == 0:
                return component.x, component.y + component.height / 2
            elif pin_index == total_pins - 1:
                return component.x + component.width, component.y + component.height / 2
            else:
                segment = (total_pins - 2)
                progress = (pin_index - 1) / segment if segment > 0 else 0
                return component.x + component.width * progress, component.y
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if clicked on a component
            for component in self.components:
                component_rect = QRect(component.x, component.y, component.width, component.height)
                if component_rect.contains(event.pos()):
                    self.selected_component = component
                    self.dragging_component = True
                    self.drag_start_pos = event.pos()
                    self.drag_offset = QPoint(event.pos().x() - component.x, event.pos().y() - component.y)
                    self.update()
                    return
            
            # Check if clicked on a pin
            pin, pin_type, component = self.find_pin_at_position(event.pos())
            if pin:
                if not self.drawing_connection:
                    # Start drawing a connection
                    self.drawing_connection = True
                    self.connection_start_pin = (pin, pin_type, component)
                    self.connection_end_pos = event.pos()
                else:
                    # Complete the connection
                    start_pin, start_type, start_component = self.connection_start_pin
                    end_pin, end_type, end_component = pin, pin_type, component
                    
                    # Don't connect a pin to itself
                    if start_pin.id != end_pin.id:
                        # Create the connection
                        connection = Connection(
                            f"connection_{self.next_connection_id}",
                            start_pin.id,
                            end_pin.id
                        )
                        self.next_connection_id += 1
                        self.connections.append(connection)
                    
                    # Reset connection drawing state
                    self.drawing_connection = False
                    self.connection_start_pin = None
                    self.update()
                return
            
            # If clicked on empty space and drawing a connection, cancel it
            if self.drawing_connection:
                self.drawing_connection = False
                self.connection_start_pin = None
                self.update()
            
            # Deselect component if clicked on empty space
            self.selected_component = None
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.dragging_component and self.selected_component:
            # Move the component
            self.selected_component.x = event.pos().x() - self.drag_offset.x()
            self.selected_component.y = event.pos().y() - self.drag_offset.y()
            self.update()
        
        if self.drawing_connection:
            # Update the end position of the connection line
            self.connection_end_pos = event.pos()
            self.update()
        
        # Update hovered pin
        pin, pin_type, component = self.find_pin_at_position(event.pos())
        if pin != self.hovered_pin:
            self.hovered_pin = pin
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_component = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the board background
        board_rect = QRect(50, 50, self.board.width, self.board.height)
        painter.fillRect(board_rect, QColor(100, 100, 100))
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawRect(board_rect)
        
        # Draw board name
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(board_rect, Qt.AlignCenter, self.board.name)
        
        # Draw board pins
        for pin in self.board.pins:
            self.draw_pin(painter, pin, "board")
        
        # Draw components
        component_types = ComponentDefinitions.get_component_types()
        for component in self.components:
            comp_def = next((c for c in component_types if c["id"] == component.type_name), None)
            if comp_def:
                # Draw component background
                component_rect = QRect(component.x, component.y, component.width, component.height)
                painter.fillRect(component_rect, QColor(comp_def["color"]))
                
                # Highlight selected component
                if component == self.selected_component:
                    painter.setPen(QPen(Qt.white, 2))
                else:
                    painter.setPen(QPen(QColor(50, 50, 50), 1))
                
                painter.drawRect(component_rect)
                
                # Draw component name and icon
                painter.setPen(Qt.white)
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                painter.drawText(component_rect, Qt.AlignCenter, f"{comp_def['icon']}\n{comp_def['name']}")
                
                # Draw component pins
                for pin in component.pins:
                    pin_pos = self.calculate_pin_position(pin, component)
                    pin.x, pin.y = pin_pos[0], pin_pos[1]
                    self.draw_pin(painter, pin, "component")
        
        # Draw connections
        for connection in self.connections:
            # Find the source and target pins
            source_pin_obj = None
            target_pin_obj = None
            
            # Check board pins first
            for pin in self.board.pins:
                if pin.id == connection.source_pin:
                    source_pin_obj = pin
                if pin.id == connection.target_pin:
                    target_pin_obj = pin
            
            # Check component pins
            for component in self.components:
                for pin in component.pins:
                    if pin.id == connection.source_pin:
                        source_pin_obj = pin
                    if pin.id == connection.target_pin:
                        target_pin_obj = pin
            
            if source_pin_obj and target_pin_obj:
                # Draw the connection line
                painter.setPen(QPen(QColor(255, 193, 7), 2, Qt.DashLine))
                self.draw_connection_line(painter, source_pin_obj.x, source_pin_obj.y, 
                                        target_pin_obj.x, target_pin_obj.y)
        
        # Draw connection being created
        if self.drawing_connection:
            start_pin, start_type, start_component = self.connection_start_pin
            if start_type == "board":
                start_x, start_y = start_pin.x, start_pin.y
            else:
                start_x, start_y = self.calculate_pin_position(start_pin, start_component)
            
            painter.setPen(QPen(QColor(255, 193, 7), 2, Qt.DotLine))
            self.draw_connection_line(painter, start_x, start_y, 
                                    self.connection_end_pos.x(), self.connection_end_pos.y())
    
    def draw_pin(self, painter, pin, pin_type):
        # Determine pin color based on type
        if pin_type == "board":
            pin_color = self.pin_colors.get(pin.type, QColor(0, 0, 0))
        else:
            pin_color = QColor(255, 235, 59)  # Yellow for component pins
        
        # Draw pin circle
        pin_size = 8 if pin == self.hovered_pin else 6
        painter.setBrush(QBrush(pin_color))
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        
        # Convert coordinates to integers
        x = int(pin.x)
        y = int(pin.y)
        painter.drawEllipse(QPoint(x, y), pin_size // 2, pin_size // 2)
        
        # Draw pin label for board pins
        if pin_type == "board":
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 7))
            
            # Determine label position based on pin location
            if pin.x < 100:  # Left side
                painter.drawText(x + 8, y + 4, pin.name)
            elif pin.x > 200:  # Right side
                text_width = painter.fontMetrics().horizontalAdvance(pin.name)
                painter.drawText(x - text_width - 8, y + 4, pin.name)
            else:  # Bottom
                painter.drawText(x - 10, y - 8, pin.name)
    
    def draw_connection_line(self, painter, x1, y1, x2, y2):
        # Draw a curved connection line between two points
        path = QPainterPath()
        path.moveTo(x1, y1)
        
        # Calculate control points for the cubic bezier curve
        dx = x2 - x1
        control_x1 = x1 + dx * 0.3
        control_y1 = y1
        control_x2 = x2 - dx * 0.3
        control_y2 = y2
        
        path.cubicTo(control_x1, control_y1, control_x2, control_y2, x2, y2)
        painter.drawPath(path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-component"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-component"):
            component_type = event.mimeData().text()
            component = self.add_component(component_type)
            if component:
                component.x = event.pos().x() - component.width // 2
                component.y = event.pos().y() - component.height // 2
                self.update()
            event.acceptProposedAction()
    
    def contextMenuEvent(self, event):
        # Create context menu
        menu = QMenu(self)
        
        # Check if right-clicked on a component
        for component in self.components:
            component_rect = QRect(int(component.x), int(component.y), int(component.width), int(component.height))
            if component_rect.contains(event.pos()):
                # Component context menu
                delete_action = menu.addAction("Delete Component")
                delete_action.triggered.connect(lambda checked=False, c=component: self.delete_component(c))
                menu.exec_(event.globalPos())
                return
        
        # Check if right-clicked on a connection
        for connection in self.connections:
            # Find the source and target pins
            source_pin_obj = None
            target_pin_obj = None
            
            for pin in self.board.pins:
                if pin.id == connection.source_pin:
                    source_pin_obj = pin
                if pin.id == connection.target_pin:
                    target_pin_obj = pin
            
            for component in self.components:
                for pin in component.pins:
                    if pin.id == connection.source_pin:
                        source_pin_obj = pin
                    if pin.id == connection.target_pin:
                        target_pin_obj = pin
            
            if source_pin_obj and target_pin_obj:
                # Check if click position is near the connection line
                line_rect = QRect(
                    min(int(source_pin_obj.x), int(target_pin_obj.x)) - 5,
                    min(int(source_pin_obj.y), int(target_pin_obj.y)) - 5,
                    abs(int(source_pin_obj.x) - int(target_pin_obj.x)) + 10,
                    abs(int(source_pin_obj.y) - int(target_pin_obj.y)) + 10
                )
                
                if line_rect.contains(event.pos()):
                    delete_action = menu.addAction("Delete Connection")
                    delete_action.triggered.connect(lambda checked=False, c=connection: self.delete_connection(c))
                    menu.exec_(event.globalPos())
                    return
        
        # Default canvas context menu
        add_menu = menu.addMenu("Add Component")
        for comp_type in ComponentDefinitions.get_component_types():
            action = add_menu.addAction(comp_type["name"])
            action.triggered.connect(lambda checked=False, ct=comp_type["id"]: self.add_component(ct))
        
        menu.exec_(event.globalPos())
    
    def delete_component(self, component):
        # Remove all connections to this component
        self.connections = [c for c in self.connections 
                           if not (c.source_pin.startswith(component.id) or 
                                  c.target_pin.startswith(component.id))]
        
        # Remove the component
        self.components.remove(component)
        if self.selected_component == component:
            self.selected_component = None
        
        self.update()
    
    def delete_connection(self, connection):
        self.connections.remove(connection)
        self.update()

class ComponentListItem(QListWidgetItem):
    def __init__(self, component_type, parent=None):
        super().__init__(parent)
        self.component_type = component_type
        self.setText(component_type["name"])
        self.setIcon(QIcon())  # You could add actual icons here

class ComponentList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        
        # Add component types
        for comp_type in ComponentDefinitions.get_component_types():
            item = ComponentListItem(comp_type)
            self.addItem(item)
    
    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item:
            mime_data = QMimeData()
            mime_data.setData("application/x-component", QByteArray())
            mime_data.setText(item.component_type["id"])
            
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Create a pixmap for drag visualization
            pixmap = QPixmap(80, 60)
            pixmap.fill(QColor(item.component_type["color"]))
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(40, 30))
            
            drag.exec_(Qt.CopyAction)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Microcontroller IDE")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        
        # Serial monitor
        self.serial_monitor = None
        self.available_ports = []
        self.update_ports()
    
    def setup_ui(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Board selection
        self.board_combo = QComboBox()
        self.board_combo.addItems(["Arduino Uno", "ESP32", "Teensy 4.0", "Daisy Seed"])
        self.board_combo.currentIndexChanged.connect(self.change_board)
        self.toolbar.addWidget(QLabel("Board: "))
        self.toolbar.addWidget(self.board_combo)
        self.toolbar.addSeparator()
        
        # Serial port selection
        self.port_combo = QComboBox()
        self.toolbar.addWidget(QLabel("Port: "))
        self.toolbar.addWidget(self.port_combo)
        
        refresh_ports_action = QAction("Refresh", self)
        refresh_ports_action.triggered.connect(self.update_ports)
        self.toolbar.addAction(refresh_ports_action)
        self.toolbar.addSeparator()
        
        # Add other toolbar actions
        compile_action = QAction("Generate Code", self)
        compile_action.triggered.connect(self.generate_code)
        self.toolbar.addAction(compile_action)
        
        upload_action = QAction("Upload", self)
        upload_action.triggered.connect(self.upload_code)
        self.toolbar.addAction(upload_action)
        
        self.toolbar.addSeparator()
        
        serial_monitor_action = QAction("Serial Monitor", self)
        serial_monitor_action.triggered.connect(self.toggle_serial_monitor)
        self.toolbar.addAction(serial_monitor_action)
        
        # Main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Component list panel
        self.component_panel = QWidget()
        self.component_layout = QVBoxLayout(self.component_panel)
        self.component_layout.addWidget(QLabel("Components"))
        
        self.component_list = ComponentList()
        self.component_layout.addWidget(self.component_list)
        
        # Canvas area
        self.canvas_area = QScrollArea()
        self.canvas = BoardCanvas()
        self.canvas_area.setWidget(self.canvas)
        self.canvas_area.setWidgetResizable(True)
        
        # Code and serial output tabs
        self.output_tabs = QTabWidget()
        
        # Code tab
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Courier New", 10))
        self.output_tabs.addTab(self.code_editor, "Generated Code")
        
        # Serial output tab
        self.serial_output = QTextEdit()
        self.serial_output.setReadOnly(True)
        self.serial_output.setFont(QFont("Courier New", 10))
        self.output_tabs.addTab(self.serial_output, "Serial Monitor")
        
        # Add components to the main splitter
        self.main_splitter.addWidget(self.component_panel)
        self.main_splitter.addWidget(self.canvas_area)
        self.main_splitter.addWidget(self.output_tabs)
        
        # Set splitter sizes
        self.main_splitter.setSizes([200, 700, 300])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def change_board(self, index):
        board_types = ["arduino", "esp32", "teensy", "daisy"]
        if index >= 0 and index < len(board_types):
            self.canvas.change_board(board_types[index])
    
    def generate_code(self):
        # Get board type
        board_index = self.board_combo.currentIndex()
        board_types = ["arduino", "esp32", "teensy", "daisy"]
        board_type = board_types[board_index] if board_index < len(board_types) else "arduino"
        
        # Generate code
        code = CodeGenerator.generate_code(board_type, self.canvas.components, self.canvas.connections)
        self.code_editor.setText(code)
        self.output_tabs.setCurrentIndex(0)
        
        self.statusBar().showMessage("Code generated")
    
    def upload_code(self):
        # Get selected port
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Error", "No serial port selected")
            return
        
        # Get current code
        code = self.code_editor.toPlainText()
        if not code:
            QMessageBox.warning(self, "Error", "No code to upload")
            return
        
        # Save code to temporary file
        temp_file = os.path.join(os.path.expanduser("~"), "temp_microcontroller_code.ino")
        with open(temp_file, "w") as f:
            f.write(code)
        
        # Get board type
        board_index = self.board_combo.currentIndex()
        board_types = ["arduino:avr:uno", "esp32:esp32:esp32", "teensy:avr:teensy40", "daisy:stm32:daisy"]
        board_type = board_types[board_index] if board_index < len(board_types) else "arduino:avr:uno"
        
        # In a real implementation, you would use a library like pyserial or subprocess to call Arduino CLI
        # For demonstration, just show a message
        msg = f"Code would be uploaded to {port} for board {board_type}"
        QMessageBox.information(self, "Upload", msg)
        
        self.statusBar().showMessage("Upload completed")
    
    def update_ports(self):
        self.port_combo.clear()
        self.available_ports = []
        
        # Get list of available serial ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)
            self.available_ports.append(port.device)
        
        if not self.available_ports:
            self.statusBar().showMessage("No serial ports found")
        else:
            self.statusBar().showMessage(f"Found {len(self.available_ports)} serial ports")
    
    def toggle_serial_monitor(self):
        # If serial monitor is running, stop it
        if self.serial_monitor and self.serial_monitor.isRunning():
            self.serial_monitor.stop()
            self.serial_monitor.wait()
            self.serial_monitor = None
            self.statusBar().showMessage("Serial monitor stopped")
            return
        
        # Get selected port
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Error", "No serial port selected")
            return
        
        # Start serial monitor
        try:
            self.serial_monitor = SerialMonitor(port, 9600)
            self.serial_monitor.data_received.connect(self.update_serial_output)
            self.serial_monitor.start()
            
            self.serial_output.clear()
            self.serial_output.append(f"Connected to {port} at 9600 baud")
            self.output_tabs.setCurrentIndex(1)
            
            self.statusBar().showMessage("Serial monitor running")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open serial port: {str(e)}")
    
    def update_serial_output(self, data):
        self.serial_output.append(data)
        # Auto-scroll to bottom
        scrollbar = self.serial_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        # Stop serial monitor if running
        if self.serial_monitor and self.serial_monitor.isRunning():
            self.serial_monitor.stop()
            self.serial_monitor.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())