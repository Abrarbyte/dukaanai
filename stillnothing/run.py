"""
Shop Manager SaaS — Entry Point
Run with: python run.py
"""
import os
import sys
from dotenv import load_dotenv

# Force UTF-8 output on Windows so emoji/unicode prints correctly
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load environment variables first
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    print(f"\n[ShopManager] API running on http://localhost:{port}")
    print(f"[ENV] {os.environ.get('FLASK_ENV', 'development')}  |  Debug: {debug}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
