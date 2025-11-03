#!/usr/bin/env python3
import sys
import os
import json
import logging

# Add parent directory to path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import USBAnalyzer
from modules.mobile_embedded_tools import USBAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_usb')

def load_json_file(path):
    """Helper to load and log JSON file contents."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {path} successfully")
            if isinstance(data, dict):
                logger.info(f"Keys in {os.path.basename(path)}: {list(data.keys())}")
            return data
    except Exception as e:
        logger.error(f"Error loading {path}: {str(e)}")
        return None

def test_vendor_lookup(analyzer, vendor_id):
    """Test vendor lookup and log detailed results."""
    logger.info(f"\n{'='*50}")
    logger.info(f"Testing vendor lookup for: 0x{vendor_id}")
    
    # Try different formats of the vendor ID
    test_cases = [
        vendor_id,                     # as-is
        f"0x{vendor_id}",             # with 0x prefix
        vendor_id.upper(),             # uppercase
        vendor_id.lower(),             # lowercase
        f"0x{vendor_id.upper()}",     # with 0x and uppercase
        f"0x{vendor_id.lower()}",     # with 0x and lowercase
    ]
    
    for test_case in test_cases:
        try:
            result = analyzer.get_vendor_name(test_case)
            logger.info(f"Lookup '{test_case}': {result}")
        except Exception as e:
            logger.error(f"Error looking up '{test_case}': {str(e)}")
    
    # Check database directly
    logger.info("\nDirect database check:")
    vendor_key = vendor_id.upper().replace('0X', '')
    if vendor_key in analyzer.vendor_db:
        logger.info(f"Found direct match for {vendor_key}: {analyzer.vendor_db[vendor_key]}")
    else:
        logger.warning(f"No direct match for {vendor_key} in vendor_db")
        
    # Try case-insensitive search
    for k, v in analyzer.vendor_db.items():
        if k.upper().replace('0X', '') == vendor_key:
            logger.info(f"Found case-insensitive match: {k} = {v}")
            break
    else:
        logger.warning(f"No case-insensitive match found for {vendor_key}")

def test_device_lookup(analyzer, vendor_id, product_id):
    """Test device lookup and log detailed results."""
    logger.info(f"\n{'='*50}")
    logger.info(f"Testing device lookup for: 0x{vendor_id}/0x{product_id}")
    
    # Try different formats of the IDs
    test_cases = [
        (vendor_id, product_id),                     # as-is
        (f"0x{vendor_id}", f"0x{product_id}"),     # with 0x prefix
        (vendor_id.upper(), product_id.upper()),     # uppercase
        (vendor_id.lower(), product_id.lower()),     # lowercase
        (f"0x{vendor_id.upper()}", f"0x{product_id.upper()}"),  # with 0x and uppercase
        (f"0x{vendor_id.lower()}", f"0x{product_id.lower()}"),  # with 0x and lowercase
    ]
    
    for v, p in test_cases:
        try:
            result = analyzer.get_device_info(v, p)
            logger.info(f"Lookup '0x{v}/0x{p}': {result}")
        except Exception as e:
            logger.error(f"Error looking up '0x{v}/0x{p}': {str(e)}")

def main():
    # Check if we're running in a GUI environment
    gui_env = 'PyQt5.QtWidgets' in sys.modules
    
    # Only create QApplication if we're in a GUI environment
    app = None
    if gui_env:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
    
    analyzer = None
    try:
        logger.info("Starting USB Analyzer test...")
        
        # Create analyzer instance
        logger.info("Creating USBAnalyzer instance...")
        analyzer = USBAnalyzer()
        
        # Test with Linux Foundation (0x1d6b) - should be in the database
        test_vendor_lookup(analyzer, '1d6b')
        test_device_lookup(analyzer, '1d6b', '0002')  # 2.0 root hub
        
        # Test with another known vendor (e.g., Intel)
        test_vendor_lookup(analyzer, '8086')
        
        # Print database stats
        logger.info("\nDatabase statistics:")
        logger.info(f"Vendors loaded: {len(analyzer.vendor_db)}")
        logger.info(f"Device categories loaded: {len(analyzer.device_db)}")
        
        # Print first few vendors for verification
        logger.info("\nFirst 5 vendors in database:")
        for i, (vid, name) in enumerate(analyzer.vendor_db.items()):
            if i >= 5:
                break
            logger.info(f"  {vid}: {name}")
        
        logger.info("\nTest completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return 1
    finally:
        # Clean up resources
        if analyzer is not None:
            if hasattr(analyzer, 'deleteLater'):
                analyzer.deleteLater()
            elif hasattr(analyzer, 'close'):
                analyzer.close()
        
        # Clean up QApplication if we created it
        if gui_env and app is not None and QApplication.instance() is not None:
            QApplication.quit()
            
        # Force Python to clean up
        import gc
        gc.collect()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
