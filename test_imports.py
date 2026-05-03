#!/usr/bin/env python3
"""
Test script to identify import issues in ProcureIQ
"""

def test_imports():
    """Test all imports to find issues."""
    errors = []

    # Test standard library imports
    try:
        import asyncio, concurrent, html, math, time
        from typing import Any, Dict, List, Optional, Tuple
        print("✓ Standard library imports OK")
    except Exception as e:
        errors.append(f"Standard library: {e}")

    # Test core third-party imports
    try:
        import numpy as np
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        import requests
        import streamlit as st
        print("✓ Core third-party imports OK")
    except Exception as e:
        errors.append(f"Core third-party: {e}")

    # Test ML imports
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        print("✓ ML imports OK")
    except Exception as e:
        errors.append(f"ML imports: {e}")

    # Test finance imports
    try:
        import yfinance as yf
        print("✓ Finance imports OK")
    except Exception as e:
        errors.append(f"Finance imports: {e}")

    # Test API imports
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        print("✓ API imports OK")
    except Exception as e:
        errors.append(f"API imports: {e}")

    # Test security imports
    try:
        import jwt
        from passlib.context import CryptContext
        print("✓ Security imports OK")
    except Exception as e:
        errors.append(f"Security imports: {e}")

    # Test local imports
    try:
        from config import DIMENSIONS
        from taxonomy import CATEGORY_TAXONOMY
        print("✓ Local config imports OK")
    except Exception as e:
        errors.append(f"Local config imports: {e}")

    # Test database imports
    try:
        from database import get_database
        print("✓ Database imports OK")
    except Exception as e:
        errors.append(f"Database imports: {e}")

    # Test evaluation imports
    try:
        from evaluation import get_subcategory_weights
        print("✓ Evaluation imports OK")
    except Exception as e:
        errors.append(f"Evaluation imports: {e}")

    # Test market data imports
    try:
        from market_data import get_market_leaders
        print("✓ Market data imports OK")
    except Exception as e:
        errors.append(f"Market data imports: {e}")

    # Test advanced modules (optional) - only test if dependencies are available
    try:
        # Check if alpha_vantage is available before testing realtime_data
        import alpha_vantage
        from realtime_data import get_realtime_provider
        print("✓ Real-time data imports OK")
    except ImportError as e:
        if "alpha_vantage" in str(e):
            print("⚠ Real-time data imports skipped (alpha_vantage not available)")
        else:
            errors.append(f"Real-time data imports: {e}")

    try:
        # Check if cryptography is available before testing security
        import cryptography
        from security import get_security_manager
        print("✓ Advanced security imports OK")
    except ImportError as e:
        if "cryptography" in str(e):
            print("⚠ Advanced security imports skipped (cryptography not available)")
        else:
            errors.append(f"Advanced security imports: {e}")

    # Test main app import
    try:
        import app
        print("✓ Main app import OK")
    except Exception as e:
        errors.append(f"Main app import: {e}")

    if errors:
        print("\n❌ Import Errors Found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    test_imports()
