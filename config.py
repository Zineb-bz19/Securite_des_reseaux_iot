class Config:
    # Application settings
    APP_NAME = "Forest Monitoring System"
    APP_VERSION = "1.0.0"
    
    # Database settings
    DATABASE_FILE = "db.sqlite"
    
    # Alert thresholds - Temperature (°C)
    TEMP_LOW_THRESHOLD = 5.0          # Too cold for forest health
    TEMP_HIGH_THRESHOLD = 35.0        # High temperature warning
    TEMP_CRITICAL_THRESHOLD = 40.0    # Dangerous temperature level
    
    # Alert thresholds - Humidity (%)
    HUMIDITY_LOW_THRESHOLD = 30.0     # Too dry for forest health
    HUMIDITY_HIGH_THRESHOLD = 80.0    # High humidity warning
    HUMIDITY_CRITICAL_THRESHOLD = 20.0 # Critical dry level 
    
    # UI Colors
    PRIMARY_COLOR = "#2c3e50"         # Dark blue - for headers/navigation
    SECONDARY_COLOR = "#3498db"       # Blue - for buttons/accents
    ACCENT_COLOR = "#e74c3c"          # Red - for warnings/important actions
    BG_COLOR = "#ecf0f1"              # Light gray - background
    TEXT_COLOR = "#2c3e50"            # Dark blue - text color
    
    # UI Fonts
    TITLE_FONT = ("Arial", 18, "bold")       # Main titles
    HEADING_FONT = ("Arial", 14, "bold")     # Section headings
    BODY_FONT = ("Arial", 12)                # Regular text
    SMALL_FONT = ("Arial", 10)               # Captions, small text
    
    # Path settings
    DATA_DIR = "data"                 # Directory for CSV files
    IMAGE_DIR = "images"              # Directory for application images