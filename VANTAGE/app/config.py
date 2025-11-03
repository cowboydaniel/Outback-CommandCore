"""
Configuration settings for the Vantage application.
"""

class Config:
    # Application settings
    APP_NAME = "Vantage"
    VERSION = "1.0.0"
    
    # UI Settings
    WINDOW_TITLE = f"{APP_NAME} - CommandCore Suite"
    WINDOW_SIZE = (1200, 800)
    
    # Style Settings
    STYLESHEET = """
        /* Base styles will be defined here */
        QMainWindow {
            background-color: #2A2D2E;
            color: #ECF0F1;
        }
    """
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "vantage.log"
    
    # Add other configuration parameters as needed
