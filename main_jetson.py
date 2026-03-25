import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Jetson
import matplotlib.pyplot as plt
import pandas as pd
from ultralytics import YOLO
import easyocr
from math import atan2, degrees
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QTimer
from ui_mainwindow import Ui_MainWindow
import seaborn as sns
import os
import torch

class V4L2DeviceSelector:
    """Detect and manage V4L2 video devices - Jetson Orin Nano optimized"""
    
    @staticmethod
    def get_available_devices():
        """Get list of available V4L2 devices"""
        devices = []
        try:
            for i in range(10):
                device_path = f'/dev/video{i}'
                if os.path.exists(device_path):
                    try:
                        cap = cv2.VideoCapture(i)
                        if cap.isOpened():
                            devices.append({'path': device_path, 'index': i, 'name': f'Video Device {i}'})
                            cap.release()
                    except:
                        pass
        except Exception as e:
            print(f"Error detecting V4L2 devices: {e}")
        return devices
    
    @staticmethod
    def get_default_device():
        """Auto-detect first available camera - no blocking dialog on Jetson"""
        devices = V4L2DeviceSelector.get_available_devices()
        if devices:
            device_index = devices[0]['index']
            print(f"[Jetson] Camera detected: {devices[0]['name']} (index: {device_index})")
            return device_index
        else:
            fallback_file = "gauge_video.mp4"
            if os.path.exists(fallback_file):
                print(f"[Jetson] No camera found. Using video file: {fallback_file}")
                return fallback_file
            return 0


class GaugeReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.showFullScreen()        
        # Check GPU availability
        self.use_gpu = torch.cuda.is_available()
        if self.use_gpu:
            print(f"[Jetson] GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"[Jetson] CUDA Compute Capability: {torch.cuda.get_device_capability(0)}")
        else:
            print("[Jetson] Running on CPU mode")

        model_path = "gauge_epoch-100.pt"
        video_source = V4L2DeviceSelector.get_default_device()
        print(f"[Jetson] Video source initialized: {video_source}")
        self.rotate_180 = True
        self.current_frame = None
        self.current_annotated_frame = None

        self.ui.tableWidget_Gauge_Values.setRowCount(1)
        self.ui.tableWidget_Gauge_Values.setColumnCount(5)
        self.ui.tableWidget_Gauge_Values.setHorizontalHeaderLabels(
            ['Min Value', 'Max Value', 'Current Value', 'Converted Value', 'QR Code Data']
        )
        
        # Stretch table to match screen width
        from PySide6.QtWidgets import QHeaderView
        header = self.ui.tableWidget_Gauge_Values.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Load YOLO model - enable GPU
        self.model = YOLO(model_path)
        if self.use_gpu:
            self.model.to('cuda')
            print("[Jetson] YOLO model loaded on GPU (CUDA)")
        else:
            print("[Jetson] YOLO model loaded on CPU")
        
        self.reader = easyocr.Reader(['en'], gpu=self.use_gpu)
        self.cap = cv2.VideoCapture(video_source)
        
        # Optimize camera settings
        if isinstance(video_source, int):
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.data_buffer_size = 1000
        self.data = pd.DataFrame(columns=['Timestamp', 'Converted Value', 'QR Code Data'])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(33)

        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.append_data)
        self.record_timer.start(1000)

        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(5000)

        self.ui.pushButton_Export_CSV.clicked.connect(self.export_data)
        self.ui.pushButton_Save_Image.clicked.connect(self.save_image)

        self.qr_timer = QTimer(self)
        self.qr_timer.timeout.connect(self.read_qr_code)
        self.qr_timer.start(2000)
        
        self.ui.dateEdit_Start.dateChanged.connect(self.date_changed)
        self.ui.dateEdit_End.dateChanged.connect(self.date_changed)
        
        self.ui.preset_today.clicked.connect(self.preset_today_clicked)
        self.ui.preset_7days.clicked.connect(self.preset_7days_clicked)
        self.ui.preset_30days.clicked.connect(self.preset_30days_clicked)
        self.ui.preset_all.clicked.connect(self.preset_all_clicked)
        self.ui.preset_custom.clicked.connect(self.preset_custom_clicked)
        
        self.ui.calendar.clicked.connect(self.calendar_date_selected)
        
        self.ui.dateEdit_End.setDate(pd.Timestamp.today().date())
        self.ui.dateEdit_Start.setDate(pd.Timestamp.today().date())
        
        print("[Jetson] Application initialized successfully")

    def calculate_distance(self, point1, point2):
        return np.hypot(point1[0] - point2[0], point1[1] - point2[1])

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        if self.rotate_180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        results = self.model.predict(frame, verbose=False, imgsz=640, conf=0.10, iou=0.45, device=0 if self.use_gpu else 'cpu')
        boxes = results[0].boxes
        annotated_frame = frame.copy()

        if boxes is None or len(boxes) == 0:
            self.display_frame(annotated_frame)
            return

        # Filter and collect detections - only keep classes 0 (Center), 1 (Start), 2 (End), 3 (Tip)
        # Limit to 1 object max per class
        positions = {}
        class_counts = {}
        
        for i in range(len(boxes)):
            class_id = int(boxes.cls[i].item())
            
            # Only process Center (0), Start (1), End (2), and Tip (3) classes
            if class_id not in [0, 1, 2, 3]:
                continue
            
            # Limit to 1 object per class (keep the one with highest confidence)
            if class_id in class_counts:
                continue
            
            x1, y1, x2, y2 = boxes.xyxy[i].tolist()
            conf = float(boxes.conf[i].item()) if boxes.conf is not None else 0.0
            x, y = int((x1 + x2) / 2), int((y1 + y2) / 2)
            
            class_counts[class_id] = 1
            
            if class_id == 0:
                positions['Center'] = (x, y)
            elif class_id == 1:
                positions['Start'] = (x, y)
            elif class_id == 2:
                positions['End'] = (x, y)
            elif class_id == 3:
                positions['Tip'] = (x, y)

        # Check if all required objects are detected
        if not all(key in positions for key in ['Start', 'End', 'Tip']):
            self.display_frame(annotated_frame)
            return

        # Validate minimum distance between Start and End
        if self.calculate_distance(positions['Start'], positions['End']) < 50:
            self.display_frame(annotated_frame)
            return
        
        # Enforce positioning logic: Start must be left (smaller x), End must be right (larger x)
        # Swap if needed
        if positions['Start'][0] > positions['End'][0]:
            positions['Start'], positions['End'] = positions['End'], positions['Start']

        gauge_min_value = 0.0
        gauge_max_value = 100

        def calculate_angle(point1, point2, center):
            dx1, dy1 = point1[0] - center[0], point1[1] - center[1]
            dx2, dy2 = point2[0] - center[0], point2[1] - center[1]
            angle1 = degrees(atan2(dy1, dx1))
            angle2 = degrees(atan2(dy2, dx2))
            return (angle2 - angle1) % 360

        # Use Center as reference if available, otherwise use Start
        center = positions.get('Center', positions['Start'])
        angle_start_to_tip = calculate_angle(positions['Start'], positions['Tip'], center)
        angle_start_to_end = calculate_angle(positions['Start'], positions['End'], center)

        gauge_range = gauge_max_value - gauge_min_value
        gauge_current_value = gauge_min_value + (angle_start_to_tip / angle_start_to_end) * gauge_range if angle_start_to_end != 0 else gauge_min_value
        
        # Clamp gauge_current_value to valid range [0, 100]
        gauge_current_value = max(gauge_min_value, min(gauge_current_value, gauge_max_value))

        self.ui.tableWidget_Gauge_Values.setItem(0, 0, QTableWidgetItem(f"{gauge_min_value:.2f}%"))
        self.ui.tableWidget_Gauge_Values.setItem(0, 1, QTableWidgetItem(f"{gauge_max_value:.2f}%"))
        self.ui.tableWidget_Gauge_Values.setItem(0, 2, QTableWidgetItem(f"{gauge_current_value:.2f}%"))
        self.ui.tableWidget_Gauge_Values.setItem(0, 3, QTableWidgetItem(f"{self.convert_gauge_values(gauge_current_value):.4f}  MPa"))

        # Draw detections with red circles and blue text
        for key, (x, y) in positions.items():
            if key == 'Center':
                # Blue circle for center (BGR format: 255, 0, 0)
                cv2.circle(annotated_frame, (x, y), 6, (255, 0, 0), -1)
                cv2.putText(
                    annotated_frame,
                    key,
                    (x + 10, max(y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA
                )
            else:
                # Red circles for other points (BGR format: 0, 0, 255)
                cv2.circle(annotated_frame, (x, y), 6, (0, 0, 255), -1)
                # Blue text (BGR format: 255, 0, 0)
                cv2.putText(
                    annotated_frame,
                    key,
                    (x + 10, max(y - 10, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA
                )
        
        self.display_frame(annotated_frame)

    def display_frame(self, frame):
        self.current_annotated_frame = frame.copy()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        frame_rgb = np.ascontiguousarray(frame)
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.ui.label_Guage_Video.setPixmap(pixmap)

    def convert_gauge_values(self, gauge_current_value):
        converted_value = 1 - (gauge_current_value / 100)
        converted_value = converted_value / 10
        return max(0, min(converted_value, 1))

    def append_data(self):
        if self.ui.tableWidget_Gauge_Values.item(0, 3):
            converted_value_text = self.ui.tableWidget_Gauge_Values.item(0, 3).text()
            try:
                converted_value = float(converted_value_text.split()[0])
                timestamp = pd.Timestamp.now()
                new_index = len(self.data)
                self.data.loc[new_index] = [timestamp, converted_value, "N/A"]
                if len(self.data) > self.data_buffer_size:
                    self.data = self.data.iloc[-self.data_buffer_size:].reset_index(drop=True)
            except ValueError:
                pass

    def update_plot(self):
        if not self.data.empty:
            plt.figure(figsize=(5, 4))
            self.data.boxplot(column='Converted Value', by='QR Code Data', grid=False)
            plt.ylabel('Converted Value (MPa)')
            plt.tight_layout()
            plt.savefig('temp_plot.png')
            plt.close('all')
            pixmap = QPixmap('temp_plot.png')
            self.ui.label_Past_Records_Graph.setPixmap(pixmap)

    def export_data(self):
        if not self.data.empty:
            try:
                existing_data = pd.read_csv('gauge_data.csv')
                combined_data = pd.concat([existing_data, self.data]).drop_duplicates().reset_index(drop=True)
                combined_data.to_csv('gauge_data.csv', index=False)
            except FileNotFoundError:
                self.data.to_csv('gauge_data.csv', index=False)

    def save_image(self):
        """Save current annotated frame as PNG with timestamp filename"""
        if self.current_annotated_frame is not None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gauge_frame_{timestamp}.png"
            cv2.imwrite(filename, self.current_annotated_frame)
            print(f"[Jetson] Image saved: {filename}")

    def read_qr_code(self):
        ret, frame = self.cap.read()
        if ret:
            if self.rotate_180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            qr_detector = cv2.QRCodeDetector()
            data, _, _ = qr_detector.detectAndDecode(frame)
            if data:
                self.ui.tableWidget_Gauge_Values.setItem(0, 4, QTableWidgetItem(data))

    def uncheck_all_presets(self):
        self.ui.preset_today.setChecked(False)
        self.ui.preset_7days.setChecked(False)
        self.ui.preset_30days.setChecked(False)
        self.ui.preset_all.setChecked(False)
        self.ui.preset_custom.setChecked(False)
        self.ui.calendar.setVisible(False)
    
    def preset_today_clicked(self):
        self.uncheck_all_presets()
        self.ui.preset_today.setChecked(True)
        today = pd.Timestamp.today().date()
        self.ui.dateEdit_Start.setDate(today)
        self.ui.dateEdit_End.setDate(today)
        self.date_changed()
    
    def preset_7days_clicked(self):
        self.uncheck_all_presets()
        self.ui.preset_7days.setChecked(True)
        end_date = pd.Timestamp.today().date()
        start_date = (pd.Timestamp.today() - pd.Timedelta(days=6)).date()
        self.ui.dateEdit_Start.setDate(start_date)
        self.ui.dateEdit_End.setDate(end_date)
        self.date_changed()
    
    def preset_30days_clicked(self):
        self.uncheck_all_presets()
        self.ui.preset_30days.setChecked(True)
        end_date = pd.Timestamp.today().date()
        start_date = (pd.Timestamp.today() - pd.Timedelta(days=29)).date()
        self.ui.dateEdit_Start.setDate(start_date)
        self.ui.dateEdit_End.setDate(end_date)
        self.date_changed()
    
    def preset_all_clicked(self):
        self.uncheck_all_presets()
        self.ui.preset_all.setChecked(True)
        if not self.data.empty:
            min_date = self.data['Timestamp'].min().date()
            max_date = self.data['Timestamp'].max().date()
            self.ui.dateEdit_Start.setDate(min_date)
            self.ui.dateEdit_End.setDate(max_date)
        self.date_changed()
    
    def preset_custom_clicked(self):
        self.uncheck_all_presets()
        self.ui.preset_custom.setChecked(True)
        self.ui.calendar.setVisible(not self.ui.calendar.isVisible())
    
    def calendar_date_selected(self, date):
        self.ui.dateEdit_Start.setDate(date)
        self.ui.dateEdit_End.setDate(date)
        self.date_changed()

    def date_changed(self):
        self.ui.label_Selected_Graph.clear()
        from datetime import datetime, date
        
        start_q_date = self.ui.dateEdit_Start.date()
        end_q_date = self.ui.dateEdit_End.date()
        start_date = date(start_q_date.year(), start_q_date.month(), start_q_date.day())
        end_date = date(end_q_date.year(), end_q_date.month(), end_q_date.day())
        
        if not self.data.empty:
            start_date_ts = pd.Timestamp(datetime.combine(start_date, datetime.min.time()))
            end_date_ts = pd.Timestamp(datetime.combine(end_date, datetime.min.time())) + pd.Timedelta(days=1)
            mask = (self.data['Timestamp'] >= start_date_ts) & (self.data['Timestamp'] < end_date_ts)
            filtered_data = self.data.loc[mask]
            if not filtered_data.empty:
                plt.figure(figsize=(5, 4))
                filtered_data.boxplot(column='Converted Value', by='QR Code Data', grid=False)
                plt.ylabel('Converted Value (MPa)')
                plt.tight_layout()
                plt.savefig('temp_selected_plot.png')
                plt.close('all')
                pixmap = QPixmap('temp_selected_plot.png')
                self.ui.label_Selected_Graph.setPixmap(pixmap)

def main():
    app = QApplication([])
    try:
        with open('styles.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("[Jetson] Warning: styles.qss not found.")
    
    window = GaugeReaderApp()
    app.exec()

if __name__ == "__main__":
    main()
