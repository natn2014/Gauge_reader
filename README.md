# Vacuum Bag Gauge Reader

A desktop application that uses AI-powered computer vision to read and analyze vacuum bag gauge values in real-time.

## Features

- **Real-time Gauge Detection**: Uses YOLOv8 deep learning model to detect gauge components (center, start, end, needle tip)
- **Angle Calculation**: Calculates the gauge needle angle to determine current pressure values
- **Value Conversion**: Converts raw gauge readings (0-100%) to pressure values in MPa
- **QR Code Reading**: Detects and reads QR codes from video frames for data labeling
- **Data Recording**: Automatically captures timestamp, converted values, and QR code data
- **Data Export**: Exports collected data to CSV format for analysis
- **Date Range Filtering**: View and analyze gauge data within specific date ranges
- **Visualization**: Generates box plots showing data distribution by QR code labels
- **Memory Efficient**: Uses rolling buffer (max 1000 rows) to manage memory usage

## Requirements

- Python 3.8+
- Windows OS
- Video file named `gauge_video.mp4`
- Trained YOLO model file named `gauge_epoch-100.pt`

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
```

## Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install opencv-python numpy matplotlib pandas ultralytics easyocr PySide6 seaborn
```

3. Place the following files in the project directory:
   - `gauge_epoch-100.pt` - Trained YOLO model
   - `gauge_video.mp4` - Video file to process

## Usage

Run the application:
```bash
python main.py
```

### GUI Controls

- **Video Display Panel**: Shows real-time gauge detection with annotated markers
- **Gauge Values Table**: Displays current min/max values, current reading, and converted pressure
- **QR Code Data**: Field showing detected QR code information
- **Past Records Graph**: Box plot of all recorded data
- **Date Range Selection**: Select start and end dates to filter and view specific data
- **Selected Graph**: Box plot filtered by the selected date range
- **Export CSV**: Button to save accumulated data to `gauge_data.csv`

## How It Works

1. **Frame Processing**: Reads frames from video at 30fps
2. **Detection**: YOLOv8 model detects 4 gauge components:
   - Class 0: Center point
   - Class 1: Start position (0% mark)
   - Class 2: End position (100% mark)
   - Class 3: Needle tip
3. **Angle Calculation**: Calculates the angle from start to tip relative to the full scale
4. **Value Conversion**: Applies pressure formula to convert 0-100% scale to MPa
5. **Data Recording**: Every second, records the current reading with timestamp and QR data
6. **Visualization**: Updates plots every 5 seconds; generates plots on date changes

## Pressure Conversion Formula

```
converted_value = (1 - (gauge_current_value / 100)) / 10
Max value: 0.1 MPa
Min value: 0.0 MPa
```

## Data Output

Exported CSV contains columns:
- **Timestamp**: When the reading was recorded
- **Converted Value**: Pressure in MPa
- **QR Code Data**: Associated QR code information or "N/A"

## Performance Notes

- **Memory**: Rolling buffer maintains only recent 1000 records
- **Frame Rate**: Processes at 30fps for smooth detection
- **Recording**: Data recorded every 1 second (separate timer)
- **Plotting**: Updated every 5 seconds to avoid lag
- **File Output**: Plots saved as temporary PNG files and displayed in GUI

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
