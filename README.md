# Vacuum Bag Gauge Reader

A real-time AI-powered computer vision application for reading and analyzing vacuum bag gauge pressure values, optimized for **NVIDIA Jetson Orin Nano**.

## Features

- **Real-time Gauge Detection**: YOLOv8 deep learning model detects 4 gauge components — Center, Start, End, and Needle Tip
- **Needle Visualization**: Draws a yellow line from Center to Tip on each frame for clear needle indication
- **Angle Calculation**: Computes gauge needle angle to derive the current pressure reading
- **Value Conversion**: Converts raw gauge readings (0–100%) to pressure values in MPa
- **QR Code Reading**: Detects and decodes QR codes from video frames for data labeling
- **Data Recording**: Automatically captures timestamp, converted values, and QR code data every second
- **Data Export**: Exports collected data to CSV format for analysis
- **Date Range Filtering**: Preset filters (Today, 7 Days, 30 Days, All, Custom) and calendar picker
- **Visualization**: Box plots showing value distribution by QR code label
- **Memory Efficient**: Rolling buffer (max 1000 rows) to manage memory usage
- **GPU Acceleration**: Automatically uses CUDA GPU on Jetson if available; falls back to CPU
- **Full-Screen UI**: Launches in full-screen mode with responsive table layout

## Platform

- **Primary Target**: NVIDIA Jetson Orin Nano (JetPack, Ubuntu)
- **Camera Input**: Auto-detects V4L2 cameras (`/dev/video0`–`/dev/video9`)
- **Fallback**: Uses `gauge_video.mp4` if no camera is found

## Requirements

- Python 3.8+
- NVIDIA Jetson Orin Nano (or compatible Linux system)
- Trained YOLO model file: `gauge_epoch-100.pt`
- Camera device **or** video file `gauge_video.mp4`

## Dependencies

```
opencv-python
numpy
matplotlib
pandas
ultralytics (YOLOv8)
easyocr
PySide6
seaborn
torch (with CUDA for GPU support)
```

## Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install opencv-python numpy matplotlib pandas ultralytics easyocr PySide6 seaborn torch
```

3. Place the following files in the project directory:
   - `gauge_epoch-100.pt` — Trained YOLO model
   - `gauge_video.mp4` — (Optional) Video fallback if no camera is connected
   - `styles.qss` — Qt stylesheet for the UI

## Usage

Run the Jetson-optimized application:
```bash
python main_jetson.py
```

Or run the standard desktop version:
```bash
python main.py
```

### GUI Controls

| Element | Description |
|---|---|
| **Video Display Panel** | Live feed with annotated detection markers and yellow needle line |
| **Gauge Values Table** | Min, Max, Current (%), Converted (MPa), QR Code Data |
| **Past Records Graph** | Box plot of all recorded pressure data |
| **Date Preset Buttons** | Quick filters: Today, Last 7 Days, Last 30 Days, All, Custom |
| **Calendar** | Visible when Custom preset is selected |
| **Selected Graph** | Box plot filtered by the selected date range |
| **Export CSV** | Saves accumulated data to `gauge_data.csv` |
| **Save Image** | Saves current annotated frame as a timestamped PNG |

## How It Works

1. **Camera/Video Input**: Auto-detects V4L2 camera or falls back to a video file; frames are rotated 180° by default
2. **Detection**: YOLOv8 model identifies up to 4 gauge components per frame:
   - Class 0: **Center** — pivot reference point (blue circle)
   - Class 1: **Start** — 0% scale mark (red circle)
   - Class 2: **End** — 100% scale mark (red circle)
   - Class 3: **Tip** — needle tip (red circle)
3. **Needle Line**: A **yellow line** is drawn from Center to Tip
4. **Angle Calculation**: Computes angular position of the needle relative to Start and End
5. **Value Conversion**: Maps angle ratio to pressure in MPa
6. **Data Recording**: Every second, logs timestamp, pressure value, and QR data
7. **Visualization**: Plots refresh every 5 seconds; date-filtered plots update on demand

## Pressure Conversion Formula

$$\text{converted\_value} = \frac{1 - \frac{\text{gauge}}{100}}{10}$$

| Gauge % | Pressure (MPa) |
|---|---|
| 0% | 0.1000 MPa |
| 50% | 0.0500 MPa |
| 100% | 0.0000 MPa |

## Data Output

Exported `gauge_data.csv` contains:

| Column | Description |
|---|---|
| `Timestamp` | Date and time of the reading |
| `Converted Value` | Pressure in MPa |
| `QR Code Data` | Decoded QR label or `"N/A"` |

## Performance Notes

| Timer | Interval | Purpose |
|---|---|---|
| Frame processing | 33 ms (~30 fps) | Real-time detection |
| Data recording | 1000 ms | Pressure logging |
| Plot update | 5000 ms | Background visualization |
| QR code scan | 2000 ms | QR code detection |

- GPU (CUDA) used automatically when available on Jetson
- Camera resolution locked to 640×480 for performance
- Rolling buffer keeps only the most recent 1000 records in memory

## File Structure

```
VacuumBagGauge/
├── main.py                    # Main application
├── ui_mainwindow.py          # UI components
├── gauge_epoch-100.pt        # YOLOv8 model (not included)
├── gauge_video.mp4           # Input video (not included)
├── gauge_data.csv            # Exported data (generated)
├── temp_plot.png             # Current plot visualization (generated)
└── temp_selected_plot.png    # Filtered plot visualization (generated)
```

## Troubleshooting

- **Model not found**: Ensure `gauge_epoch-100.pt` is in the project directory
- **Video not found**: Ensure `gauge_video.mp4` is in the project directory
- **Detection issues**: Check lighting and video quality; ensure all 4 gauge components are visible
- **Memory issues**: Data buffer limits to 1000 recent records; adjust `data_buffer_size` if needed

## Future Improvements

- Support for multiple video sources
- Real-time camera input
- Custom gauge scale configuration
- Advanced filtering and analysis tools
- Database storage instead of CSV
- Multi-gauge support

## License

This project is provided as-is for educational and commercial use.
