"""Shared application singletons for consistent state across routes."""

from ai.service import AIService
from trading.order_manager import OrderManager

ai_service = AIService()
order_manager = OrderManager()
