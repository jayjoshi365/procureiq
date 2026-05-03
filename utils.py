# utils.py
# Utility functions for ProcureIQ

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import re

def sx(value, suffix: str = '') -> str:
    """Format a number with comma separators or return a string unchanged."""
    if value is None:
        return "0"
    if isinstance(value, str):
        return value
    try:
        if isinstance(value, int):
            return f"{value:,}{suffix}"
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if value == 0:
        return f"0{suffix}"
    formatted = f"{value:,.2f}".rstrip('0').rstrip('.')
    return f"{formatted}{suffix}"

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert hex color to rgba string"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6 or not re.fullmatch(r'[0-9a-fA-F]{6}', hex_color):
        return f"rgba(0, 0, 0, {alpha})"

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f"rgba({r}, {g}, {b}, {alpha})"

def format_currency(amount: float, currency: str = '$') -> str:
    """Format amount as currency"""
    return f"{currency}{amount:,.0f}"

def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division to avoid division by zero"""
    return numerator / denominator if denominator != 0 else default

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    return ((new_value - old_value) / old_value) * 100

def validate_email(email: str) -> bool:
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def get_unique_values(data: List[Dict], key: str) -> List[str]:
    """Extract unique values from list of dicts by key"""
    return list(set(item.get(key, '') for item in data if item.get(key)))

def filter_data(data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """Filter list of dicts based on criteria"""
    filtered = data
    for key, value in filters.items():
        if value is not None:
            filtered = [item for item in filtered if item.get(key) == value]
    return filtered

def sort_data(data: List[Dict], sort_key: str, reverse: bool = False) -> List[Dict]:
    """Sort list of dicts by key"""
    return sorted(data, key=lambda x: x.get(sort_key, ''), reverse=reverse)

def paginate_data(data: List[Dict], page: int, page_size: int) -> Tuple[List[Dict], int]:
    """Paginate data and return page data and total pages"""
    total_pages = (len(data) + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    return data[start_idx:end_idx], total_pages

def export_to_csv(data: List[Dict], filename: str) -> str:
    """Export data to CSV string"""
    if not data:
        return ""

    df = pd.DataFrame(data)
    return df.to_csv(index=False)

def calculate_stats(values: List[float]) -> Dict[str, float]:
    """Calculate basic statistics"""
    if not values:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0}

    return {
        "mean": np.mean(values),
        "median": np.median(values),
        "std": np.std(values),
        "min": min(values),
        "max": max(values)
    }

def generate_id(prefix: str = "", length: int = 8) -> str:
    """Generate a cryptographically secure random ID."""
    import secrets
    token = secrets.token_urlsafe(length)[:length]
    return f"{prefix}{token}" if prefix else token

def parse_date(date_str: str) -> pd.Timestamp:
    """Parse date string to pandas timestamp"""
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

def format_date(date: pd.Timestamp, format_str: str = "%Y-%m-%d") -> str:
    """Format pandas timestamp to string"""
    if pd.isna(date):
        return ""
    return date.strftime(format_str)

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ""

def is_valid_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Check if file type is allowed"""
    ext = get_file_extension(filename)
    return ext in allowed_types

def calculate_completion_percentage(completed: int, total: int) -> float:
    """Calculate completion percentage"""
    return safe_divide(completed, total, 0) * 100

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"