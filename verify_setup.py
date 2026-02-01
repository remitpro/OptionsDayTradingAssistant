"""
Quick setup verification script.
Run this to verify your installation is correct.
"""

import sys
from pathlib import Path

def verify_installation():
    """Verify that all components are installed correctly."""
    
    print("🔍 Verifying Options Trading System Installation...\n")
    
    errors = []
    warnings = []
    
    # Check Python version
    print("1. Checking Python version...")
    if sys.version_info < (3, 11):
        errors.append(f"Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    required_packages = [
        'pandas', 'numpy', 'scipy', 'tda', 'sqlalchemy',
        'pydantic', 'pydantic_settings', 'rich', 'dotenv'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            errors.append(f"Missing package: {package}")
            print(f"   ✗ {package} - NOT FOUND")
    
    # Check directory structure
    print("\n3. Checking directory structure...")
    required_dirs = [
        'config', 'src/scanner', 'src/strategies', 'src/analytics',
        'src/scoring', 'src/integration', 'src/data', 'src/utils',
        'outputs/trades', 'outputs/alerts', 'outputs/watchlists', 'logs'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✓ {dir_path}")
        else:
            errors.append(f"Missing directory: {dir_path}")
            print(f"   ✗ {dir_path} - NOT FOUND")
    
    # Check configuration
    print("\n4. Checking configuration...")
    if Path('.env').exists():
        print("   ✓ .env file exists")
        
        # Check if API key is set
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        api_key = os.getenv('TDA_API_KEY')
        if api_key and api_key != 'your_api_key_here':
            print("   ✓ TDA_API_KEY is configured")
        else:
            warnings.append("TDA_API_KEY not configured in .env")
            print("   ⚠ TDA_API_KEY needs to be set")
    else:
        warnings.append(".env file not found - copy from .env.example")
        print("   ⚠ .env file not found")
    
    # Check main modules
    print("\n5. Checking main modules...")
    modules_to_check = [
        'config.settings',
        'src.scanner.market_scanner',
        'src.scanner.options_filter',
        'src.strategies.strategy_selector',
        'src.analytics.probability',
        'src.analytics.greeks',
        'src.analytics.risk_metrics',
        'src.scoring.trade_scorer',
        'src.integration.tos_alerts',
        'src.integration.watchlist',
        'src.data.api_client',
        'src.data.cache'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"   ✓ {module}")
        except Exception as e:
            errors.append(f"Module {module} failed to import: {str(e)}")
            print(f"   ✗ {module} - ERROR")
    
    # Summary
    print("\n" + "="*60)
    if errors:
        print(f"\n❌ ERRORS FOUND ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errors and not warnings:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nYou're ready to run the trading system:")
        print("   python main.py")
    elif not errors:
        print("\n✅ INSTALLATION COMPLETE (with warnings)")
        print("\nAddress warnings above, then run:")
        print("   python main.py")
    else:
        print("\n❌ INSTALLATION INCOMPLETE")
        print("\nFix errors above, then run this script again.")
        return 1
    
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(verify_installation())
