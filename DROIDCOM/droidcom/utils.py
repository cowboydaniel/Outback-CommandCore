import logging
import platform

# Set up logging for Android Tools Module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Check if running on Windows or Linux/Mac
IS_WINDOWS = platform.system().lower() == 'windows'
