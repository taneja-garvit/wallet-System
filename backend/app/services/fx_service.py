"""
Foreign Exchange (FX) Service

Provides exchange rates for currency conversions.
Currently uses static rates defined in code, but abstracted behind 
a service layer to allow future integration with real-time FX providers.

Interview line:
"Exchange rates are currently static and defined in code, but abstracted 
behind a service so a real FX provider can be plugged in later."
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum

# Supported currencies
class Currency(str, Enum):
    USD = "USD"
    INR = "INR"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"

# Static exchange rates (base currency: USD)
# All rates are USD -> target currency
STATIC_EXCHANGE_RATES = {
    # USD conversions
    ("USD", "USD"): Decimal("1.0"),
    ("USD", "INR"): Decimal("83.0"),
    ("USD", "EUR"): Decimal("0.92"),
    ("USD", "GBP"): Decimal("0.79"),
    ("USD", "JPY"): Decimal("149.5"),
    ("USD", "AUD"): Decimal("1.52"),
    
    # EUR conversions
    ("EUR", "USD"): Decimal("1.087"),
    ("EUR", "EUR"): Decimal("1.0"),
    ("EUR", "INR"): Decimal("90.2"),
    ("EUR", "GBP"): Decimal("0.86"),
    ("EUR", "JPY"): Decimal("162.5"),
    ("EUR", "AUD"): Decimal("1.65"),
    
    # GBP conversions
    ("GBP", "USD"): Decimal("1.266"),
    ("GBP", "INR"): Decimal("105.0"),
    ("GBP", "EUR"): Decimal("1.163"),
    ("GBP", "GBP"): Decimal("1.0"),
    ("GBP", "JPY"): Decimal("189.2"),
    ("GBP", "AUD"): Decimal("1.92"),
    
    # INR conversions
    ("INR", "USD"): Decimal("0.012048"),
    ("INR", "INR"): Decimal("1.0"),
    ("INR", "EUR"): Decimal("0.011086"),
    ("INR", "GBP"): Decimal("0.00952"),
    ("INR", "JPY"): Decimal("1.801"),
    ("INR", "AUD"): Decimal("0.01831"),
    
    # JPY conversions
    ("JPY", "USD"): Decimal("0.00669"),
    ("JPY", "INR"): Decimal("0.555"),
    ("JPY", "EUR"): Decimal("0.00615"),
    ("JPY", "GBP"): Decimal("0.00529"),
    ("JPY", "JPY"): Decimal("1.0"),
    ("JPY", "AUD"): Decimal("0.01017"),
    
    # AUD conversions
    ("AUD", "USD"): Decimal("0.658"),
    ("AUD", "INR"): Decimal("54.6"),
    ("AUD", "EUR"): Decimal("0.606"),
    ("AUD", "GBP"): Decimal("0.520"),
    ("AUD", "JPY"): Decimal("98.3"),
    ("AUD", "AUD"): Decimal("1.0"),
}


class FXService:
    """
    Foreign Exchange Service for currency conversions.
    
    Design principles:
    - Abstracted behind service layer for future extensibility
    - Deterministic rates for testing and auditability
    - Thread-safe (stateless)
    """
    
    def __init__(self):
        self.provider = "STATIC"
    
    def get_exchange_rate(
        self, 
        source_currency: str, 
        target_currency: str
    ) -> Optional[Decimal]:
        """
        Get exchange rate from source to target currency.
        
        Returns:
            Decimal: Exchange rate if pair is supported
            None: If currency pair is not supported
        """
        # Validate currencies
        try:
            Currency(source_currency)
            Currency(target_currency)
        except ValueError:
            return None
        
        # Get rate from static map
        rate = STATIC_EXCHANGE_RATES.get((source_currency, target_currency))
        return rate
    
    def convert(
        self, 
        amount: Decimal, 
        source_currency: str, 
        target_currency: str
    ) -> Optional[tuple[Decimal, Decimal]]:
        """
        Convert amount from source currency to target currency.
        
        Args:
            amount: Amount to convert
            source_currency: Source currency code
            target_currency: Target currency code
        
        Returns:
            tuple[Decimal, Decimal]: (converted_amount, exchange_rate)
            None: If currency pair not supported
        """
        rate = self.get_exchange_rate(source_currency, target_currency)
        if rate is None:
            return None
        
        # Convert with 2 decimal precision for currencies
        converted_amount = (amount * rate).quantize(Decimal("0.01"))
        
        return (converted_amount, rate)
    
    def is_currency_supported(self, currency: str) -> bool:
        """Check if currency is supported"""
        try:
            Currency(currency)
            return True
        except ValueError:
            return False
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of all supported currencies"""
        return [c.value for c in Currency]
    
    def get_provider_name(self) -> str:
        """Get FX provider name for audit trail"""
        return self.provider
    
    def get_fx_timestamp(self) -> datetime:
        """Get timestamp for FX rate (for audit trail)"""
        return datetime.utcnow()


# Singleton instance
fx_service = FXService()


def get_fx_service() -> FXService:
    """Dependency injection for FX service"""
    return fx_service
