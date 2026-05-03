"""Input validation and error handling for ProcureIQ"""
import streamlit as st
from typing import Dict, List, Optional, Union, Any
import re


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ProcureIQValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_subcategory_name(name: str) -> str:
        """Validate subcategory name."""
        if not name or not isinstance(name, str):
            raise ValidationError("Subcategory name must be a non-empty string")

        if len(name.strip()) == 0:
            raise ValidationError("Subcategory name cannot be empty")

        if len(name) > 200:
            raise ValidationError("Subcategory name too long (max 200 characters)")

        return name.strip()

    @staticmethod
    def validate_kraljic_posture(posture: str) -> str:
        """Validate Kraljic posture."""
        valid_postures = ["Strategic", "Leverage", "Bottleneck", "Non-Critical"]

        if posture not in valid_postures:
            raise ValidationError(f"Invalid Kraljic posture. Must be one of: {', '.join(valid_postures)}")

        return posture

    @staticmethod
    def validate_dimension_weights(weights: Dict[str, Union[int, float]]) -> Dict[str, float]:
        """Validate dimension weights."""
        from config import DIMENSIONS

        if not isinstance(weights, dict):
            raise ValidationError("Weights must be a dictionary")

        # Check all dimensions are present
        for dim in DIMENSIONS:
            if dim not in weights:
                raise ValidationError(f"Missing weight for dimension: {dim}")

        validated_weights = {}
        for dim, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise ValidationError(f"Weight for {dim} must be a number")

            if not (1 <= weight <= 10):
                raise ValidationError(f"Weight for {dim} must be between 1 and 10")

            validated_weights[dim] = float(weight)

        return validated_weights

    @staticmethod
    def validate_supplier_count(count: Union[int, str]) -> int:
        """Validate supplier count."""
        try:
            count_int = int(count)
        except (ValueError, TypeError):
            raise ValidationError("Supplier count must be a valid number")

        if count_int < 1:
            raise ValidationError("Supplier count must be at least 1")

        if count_int > 100:
            raise ValidationError("Supplier count seems unreasonably high (max 100)")

        return count_int

    @staticmethod
    def validate_price_weight(weight: Union[float, str]) -> float:
        """Validate price weight (0.0 to 1.0)."""
        try:
            weight_float = float(weight)
        except (ValueError, TypeError):
            raise ValidationError("Price weight must be a valid number")

        if not (0.0 <= weight_float <= 1.0):
            raise ValidationError("Price weight must be between 0.0 and 1.0")

        return weight_float

    @staticmethod
    def validate_switching_cost_answer(answer: str) -> str:
        """Validate switching cost answer."""
        valid_answers = [
            "Low — easy to switch",
            "Medium — some disruption expected",
            "High — significant transition risk",
            "Very High — near-irreversible"
        ]

        if answer not in valid_answers:
            raise ValidationError(f"Invalid switching cost answer. Must be one of: {', '.join(valid_answers)}")

        return answer

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise ValidationError("Invalid email format")

        return email.strip().lower()

    @staticmethod
    def validate_file_upload(uploaded_file, allowed_extensions: List[str] = None) -> str:
        """Validate uploaded file."""
        if uploaded_file is None:
            raise ValidationError("No file uploaded")

        if allowed_extensions is None:
            allowed_extensions = ['xlsx', 'xls', 'csv']

        file_name = uploaded_file.name.lower()
        if not any(file_name.endswith(f'.{ext}') for ext in allowed_extensions):
            raise ValidationError(f"File must be one of: {', '.join(allowed_extensions)}")

        # Check file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            raise ValidationError("File too large (max 10MB)")

        return uploaded_file.name

    @staticmethod
    def validate_ticker_symbol(ticker: str) -> Optional[str]:
        """Validate stock ticker symbol."""
        if not ticker or ticker.strip() == "":
            return None

        ticker = ticker.strip().upper()

        # Basic ticker validation (1-5 uppercase letters/numbers)
        if not re.match(r'^[A-Z0-9]{1,5}$', ticker):
            raise ValidationError("Invalid ticker symbol format")

        return ticker


class ErrorHandler:
    """Error handling utilities for Streamlit app."""

    @staticmethod
    def handle_validation_error(error: ValidationError, context: str = ""):
        """Handle validation errors with user-friendly messages."""
        message = str(error)
        if context:
            message = f"{context}: {message}"

        st.error(f"❌ {message}")

    @staticmethod
    def handle_generic_error(error: Exception, context: str = "An error occurred"):
        """Handle generic errors."""
        error_msg = f"{context}: {str(error)}"
        st.error(f"❌ {error_msg}")

        # Log error for debugging (in production, use proper logging)
        print(f"ERROR: {error_msg}")

    @staticmethod
    def safe_execute(func, *args, error_msg: str = "Operation failed", **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            ErrorHandler.handle_validation_error(e, error_msg)
            return None
        except Exception as e:
            ErrorHandler.handle_generic_error(e, error_msg)
            return None


# Global instances
validator = ProcureIQValidator()
error_handler = ErrorHandler()


def validate_supplier_csv_row(row: dict, row_num: int) -> tuple:
    """Validate a single row from a supplier CSV upload.

    Returns (cleaned_row, warnings) where cleaned_row is ready to append
    and warnings is a list of human-readable issue strings (non-fatal).
    Returns (None, warnings) when the row must be skipped entirely.
    """
    import re as _re
    from config import FINANCIAL_FIELDS as _FF

    warnings: List[str] = []

    name = str(row.get("supplier_name", "")).strip()
    if not name:
        warnings.append(f"Row {row_num}: missing supplier_name — skipped")
        return None, warnings

    # Ticker
    ticker = str(row.get("ticker", "")).strip().upper()
    if ticker and not _re.match(r'^[A-Z0-9]{1,5}$', ticker):
        warnings.append(f"Row {row_num}: invalid ticker '{ticker}' — cleared")
        ticker = ""

    # Quoted price
    raw_price_str = str(row.get("quoted_price", "")).strip()
    try:
        raw_price = float(raw_price_str) if raw_price_str else 1_000_000.0
        if raw_price < 0:
            raise ValueError
    except ValueError:
        warnings.append(f"Row {row_num}: invalid quoted_price '{raw_price_str}' — defaulting to $1,000,000")
        raw_price = 1_000_000.0

    # Financial fields — map CSV column names → FINANCIAL_FIELDS keys
    _CSV_TO_FIN = {
        "years_in_business":   "Years in Business",
        "ownership_structure": "Ownership Structure",
        "revenue_trajectory":  "Revenue Trajectory",
        "recent_ma_activity":  "Recent M&A Activity",
        "payment_terms":       "Payment Terms Offered",
        "workforce_changes":   "Workforce Changes (12mo)",
    }
    fin_inputs: Dict[str, str] = {}
    for csv_col, field_name in _CSV_TO_FIN.items():
        val = str(row.get(csv_col, "")).strip()
        valid_opts = _FF[field_name]["options"]
        if val and val not in valid_opts:
            warnings.append(
                f"Row {row_num}: '{val}' not a valid option for {field_name} — cleared. "
                f"Valid: {', '.join(valid_opts)}"
            )
            val = ""
        fin_inputs[field_name] = val

    # Dimension scores — dropdowns and 1-5 sliders
    _SLA_OPTS  = ["Strong", "Moderate", "Weak"]
    _RISK_OPTS = ["Low", "Medium", "High"]
    _QUAL_OPTS = ["Strong", "Moderate", "Weak"]

    def _dropdown(csv_col: str, opts: list) -> Optional[str]:
        raw = str(row.get(csv_col, "")).strip()
        if not raw:
            return None
        for opt in opts:
            if raw.lower() == opt.lower():
                return opt
        warnings.append(
            f"Row {row_num}: '{raw}' not valid for {csv_col} — cleared. Valid: {', '.join(opts)}"
        )
        return None

    def _score_1_5(csv_col: str) -> Optional[int]:
        raw = str(row.get(csv_col, "")).strip()
        if not raw:
            return None
        try:
            v = int(round(float(raw)))
            if not 1 <= v <= 5:
                warnings.append(f"Row {row_num}: {csv_col} value {v} out of range — clamped to 1-5")
                v = max(1, min(5, v))
            return v
        except ValueError:
            warnings.append(f"Row {row_num}: invalid {csv_col} '{raw}' — skipped")
            return None

    scores = {
        "sla":          _dropdown("sla_strength",             _SLA_OPTS),
        "risk":         _dropdown("execution_risk",           _RISK_OPTS),
        "stake":        _score_1_5("stakeholder_confidence"),
        "strategic":    _score_1_5("strategic_alignment"),
        "innovation":   _score_1_5("innovation_capacity"),
        "relationship": _score_1_5("relationship_depth"),
        "flexibility":  _score_1_5("commercial_flexibility"),
        "esg":          _dropdown("esg_sustainability",       _QUAL_OPTS),
        "diversity":    _dropdown("supplier_diversity",       _QUAL_OPTS),
    }

    cleaned = {
        "supplier_name": name,
        "ticker": ticker,
        "raw_price": raw_price,
        "notes": str(row.get("notes", "")).strip(),
        "fin_inputs": fin_inputs,
        "scores": scores,
    }
    return cleaned, warnings


def validate_all_inputs(**kwargs) -> Dict[str, Any]:
    """Validate all common inputs at once."""
    validated = {}

    for key, value in kwargs.items():
        try:
            if key == 'subcategory_name':
                validated[key] = validator.validate_subcategory_name(value)
            elif key == 'kraljic':
                validated[key] = validator.validate_kraljic_posture(value)
            elif key == 'weights':
                validated[key] = validator.validate_dimension_weights(value)
            elif key == 'supplier_count':
                validated[key] = validator.validate_supplier_count(value)
            elif key == 'price_weight':
                validated[key] = validator.validate_price_weight(value)
            elif key == 'switching_cost':
                validated[key] = validator.validate_switching_cost_answer(value)
            elif key == 'email':
                validated[key] = validator.validate_email(value)
            elif key == 'ticker':
                validated[key] = validator.validate_ticker_symbol(value)
            else:
                validated[key] = value  # Pass through unvalidated
        except ValidationError as e:
            error_handler.handle_validation_error(e, f"Invalid {key}")
            return {}

    return validated