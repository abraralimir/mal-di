"""Utility script to test system components"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_torch():
    """Test PyTorch and CUDA"""
    try:
        import torch
        logger.info(f"✓ PyTorch version: {torch.__version__}")
        logger.info(f"✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
            logger.info(f"✓ CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        return True
    except Exception as e:
        logger.error(f"✗ PyTorch test failed: {e}")
        return False

def test_ocr():
    """Test OCR pipeline"""
    try:
        from paddleocr import PaddleOCR
        logger.info("✓ Testing OCR initialization...")
        ocr = PaddleOCR(use_gpu=True, lang='en_ar')
        logger.info("✓ OCR pipeline initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ OCR test failed: {e}")
        return False

def test_transformers():
    """Test Transformers library"""
    try:
        from transformers import AutoTokenizer, AutoModel
        logger.info("✓ Transformers library available")
        return True
    except Exception as e:
        logger.error(f"✗ Transformers test failed: {e}")
        return False

def test_api():
    """Test FastAPI server"""
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            logger.info("✓ API is running and responding")
            data = response.json()
            logger.info(f"  Models loaded: {data['models_loaded']}")
            return True
        else:
            logger.error(f"✗ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning("⚠ API not running (start backend first)")
        return False
    except Exception as e:
        logger.error(f"✗ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("=" * 50)
    logger.info("Testing Document Intelligence System")
    logger.info("=" * 50)
    logger.info("")
    
    results = []
    
    logger.info("Testing environment...")
    results.append(("PyTorch & CUDA", test_torch()))
    
    logger.info("")
    logger.info("Testing dependencies...")
    results.append(("OCR Pipeline", test_ocr()))
    results.append(("Transformers", test_transformers()))
    
    logger.info("")
    logger.info("Testing API...")
    results.append(("FastAPI Server", test_api()))
    
    logger.info("")
    logger.info("=" * 50)
    logger.info("Test Results:")
    logger.info("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
        if result:
            passed += 1
    
    logger.info("")
    logger.info(f"Total: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("✓ All systems ready!")
        return 0
    else:
        logger.error("✗ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
