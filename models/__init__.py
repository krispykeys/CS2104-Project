"""
Models package for Home Value Estimator Real Estate Platform
=================================================

This package contains all data models and type definitions used throughout
the Home Value Estimator platform.
"""

from .data_models import (
    PropertyAnalysis,
    QuickAnalysisResponse,
    ATTOMSearchCriteria,
    InvestmentStrategy,
    PropertyType,
    PropertySearchResult,
    PropertySearchResponse,
    MarketAnalysis,
    UserProfile
)

__all__ = [
    'PropertyAnalysis',
    'QuickAnalysisResponse', 
    'ATTOMSearchCriteria',
    'InvestmentStrategy',
    'PropertyType',
    'PropertySearchResult',
    'PropertySearchResponse', 
    'MarketAnalysis',
    'UserProfile'
]