"""Minimal async test verifying DealFinder ↔ AnalysisEngine communication using real APIs only."""

import asyncio
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from agents.deal_finder import DealFinder, PropertyAlert, AlertType, AlertPriority
from agents.analysis_engine import AnalysisEngine, PropertyFeatures


def _have_real_keys() -> bool:
    return bool(os.getenv("GEMINI_API_KEY") and os.getenv("ATTOM_API_KEY"))


@pytest.mark.asyncio
async def test_basic_agent_communication():
    if not _have_real_keys():
        pytest.skip("Skipping: real GEMINI_API_KEY & ATTOM_API_KEY required")

    engine = AnalysisEngine()
    finder = DealFinder(analysis_engine=engine)

    features = PropertyFeatures(
        address="123 Main Street, Blacksburg, VA 24060",  # Real Virginia zip code
        gla=1400,
        bedrooms=3,
        bathrooms=2.0,
        garage_spaces=1,
        lot_size=5500,
        age=12,
        condition="good",
        property_type="SFR",
        listing_price=295000
    )

    alert = PropertyAlert(
        alert_id="comm-basic-1",
        property_address=features.address,
        alert_type=AlertType.UNDERVALUED_PROPERTY,
        priority=AlertPriority.MEDIUM,
        title="Communication Smoke Test",
        description="Ensure basic analysis pipeline runs",
        key_metrics={"square_feet": features.gla},
        estimated_value=300000,
        listing_price=features.listing_price,
        confidence_score=0.4,
        property_features=features
    )

    analyzed = await finder.analyze_property_alert(alert)
    assert analyzed is not None
    assert analyzed.property_address == alert.property_address


if __name__ == "__main__":
    asyncio.run(test_basic_agent_communication())