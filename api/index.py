import sys
import os

# Menambahkan path backend agar bisa mengimpor app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
