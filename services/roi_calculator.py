# -*- coding: utf-8 -*-
"""
services/roi_calculator.py
==========================
Killer-Feature: ROI Calculator & Business Case Generator

Features:
1. Automatische ROI-Berechnung aus Briefing
2. Business Case Generierung
3. TCO-Analyse (Total Cost of Ownership)
4. Payback Period Berechnung
5. NPV/IRR für komplexe Cases
6. Visual ROI-Charts
7. Sensitivity Analysis

Author: StratGen Agent V3.5
"""
from __future__ import annotations
import os
import re
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class CostItem:
    """Ein Kostenelement."""
    name: str
    amount: float
    category: str = "Implementation"  # Implementation, Recurring, One-time
    year: int = 0  # 0 = einmalig, 1-5 = jährlich
    notes: str = ""


@dataclass
class BenefitItem:
    """Ein Nutzenelement."""
    name: str
    amount: float
    category: str = "Revenue"  # Revenue, Savings, Productivity, Risk
    year: int = 1  # Ab welchem Jahr
    probability: float = 0.8  # Wahrscheinlichkeit der Realisierung
    notes: str = ""


@dataclass
class ROICalculation:
    """ROI-Berechnungsergebnis."""
    total_investment: float
    total_benefit_year1: float
    total_benefit_3years: float
    roi_percent: float
    payback_months: float
    npv: float  # Net Present Value
    irr: float  # Internal Rate of Return
    break_even_month: int
    confidence_level: str = "Medium"


@dataclass
class BusinessCase:
    """Vollständiger Business Case."""
    title: str
    executive_summary: str
    costs: List[CostItem] = field(default_factory=list)
    benefits: List[BenefitItem] = field(default_factory=list)
    roi: Optional[ROICalculation] = None
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommendation: str = ""


# ============================================
# INDUSTRY BENCHMARKS
# ============================================

INDUSTRY_BENCHMARKS = {
    "fertigung": {
        "typical_savings": {
            "Prozessautomatisierung": (15, 30),  # 15-30% Einsparung
            "Predictive Maintenance": (20, 40),
            "Qualitätskontrolle": (10, 25),
            "Energieeffizienz": (5, 15),
        },
        "implementation_factor": 0.8,  # Typischer Impl.-Aufwand relativ zum Nutzen
        "realization_time_months": 6
    },
    "technologie": {
        "typical_savings": {
            "Automatisierung": (20, 40),
            "Cloud Migration": (15, 35),
            "DevOps": (25, 50),
            "KI/ML": (10, 30),
        },
        "implementation_factor": 0.6,
        "realization_time_months": 4
    },
    "finanzen": {
        "typical_savings": {
            "Prozessdigitalisierung": (15, 30),
            "Risikomanagement": (20, 40),
            "Compliance": (10, 20),
            "Kundenservice": (15, 25),
        },
        "implementation_factor": 0.9,
        "realization_time_months": 8
    },
    "healthcare": {
        "typical_savings": {
            "Dokumentation": (20, 35),
            "Terminplanung": (15, 25),
            "Diagnoseunterstützung": (10, 30),
            "Patientenmanagement": (15, 30),
        },
        "implementation_factor": 0.85,
        "realization_time_months": 9
    },
    "default": {
        "typical_savings": {
            "Effizienzsteigerung": (15, 30),
            "Automatisierung": (20, 40),
            "Digitalisierung": (10, 25),
        },
        "implementation_factor": 0.75,
        "realization_time_months": 6
    }
}


# ============================================
# LLM IMPORT
# ============================================

try:
    from services.llm import generate as llm_generate, is_enabled as llm_enabled
    HAS_LLM = True
except ImportError:
    llm_generate = None
    HAS_LLM = False


# ============================================
# VALUE EXTRACTION
# ============================================

def extract_numbers_from_text(text: str) -> List[Tuple[float, str]]:
    """
    Extrahiert Zahlen und Kontext aus Text.
    
    Returns:
        Liste von (Zahl, Kontext) Tuples
    """
    patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(?:€|EUR|Euro)',
        r'(\d+(?:[.,]\d+)?)\s*(?:Mio\.?|Millionen)',
        r'(\d+(?:[.,]\d+)?)\s*%',
        r'(\d+(?:[.,]\d+)?)\s*(?:k|K|Tsd\.?)',
        r'(?:ca\.?|etwa|rund)\s*(\d+(?:[.,]\d+)?)',
    ]
    
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            number = float(match.group(1).replace(",", "."))
            # Kontext extrahieren
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            results.append((number, context))
    
    return results


def estimate_project_value(
    brief: str,
    industry: str = "",
    company_size: str = "Mittelstand"
) -> Dict[str, Any]:
    """
    Schätzt den Projektwert aus dem Briefing.
    
    Returns:
        Dictionary mit estimated_value, confidence, factors
    """
    # Branchenbenchmarks
    industry_lower = industry.lower() if industry else "default"
    benchmark = None
    for ind, bench in INDUSTRY_BENCHMARKS.items():
        if ind in industry_lower:
            benchmark = bench
            break
    if not benchmark:
        benchmark = INDUSTRY_BENCHMARKS["default"]
    
    # Basis-Schätzung basierend auf Unternehmensgröße
    size_factors = {
        "startup": (50000, 200000),
        "kmu": (100000, 500000),
        "mittelstand": (200000, 1000000),
        "großunternehmen": (500000, 5000000),
    }
    
    size_lower = company_size.lower()
    base_range = size_factors.get(size_lower, size_factors["mittelstand"])
    
    # Zahlen aus Briefing extrahieren
    numbers = extract_numbers_from_text(brief)
    
    estimated_value = sum(base_range) / 2  # Mittelwert
    confidence = "Medium"
    
    if numbers:
        # Größte Zahl als Referenz
        max_number = max(n[0] for n in numbers)
        if max_number > 1000:  # Wahrscheinlich Euro
            estimated_value = max_number
            confidence = "High"
        elif max_number < 100:  # Wahrscheinlich Prozent
            # Prozent auf Basiswert anwenden
            estimated_value = base_range[1] * (max_number / 100)
            confidence = "Medium"
    
    return {
        "estimated_value": estimated_value,
        "confidence": confidence,
        "range": base_range,
        "benchmark": benchmark
    }


# ============================================
# ROI CALCULATION
# ============================================

def calculate_roi(
    costs: List[CostItem],
    benefits: List[BenefitItem],
    discount_rate: float = 0.08,
    years: int = 3
) -> ROICalculation:
    """
    Berechnet ROI und verwandte Metriken.
    
    Args:
        costs: Liste der Kosten
        benefits: Liste der Nutzen
        discount_rate: Diskontierungssatz (default 8%)
        years: Betrachtungszeitraum
    
    Returns:
        ROICalculation-Objekt
    """
    # Gesamtinvestition
    total_investment = sum(c.amount for c in costs if c.category in ["Implementation", "One-time"])
    recurring_costs = sum(c.amount for c in costs if c.category == "Recurring")
    
    # Nutzen pro Jahr (mit Wahrscheinlichkeitsgewichtung)
    benefit_year1 = sum(b.amount * b.probability for b in benefits if b.year <= 1)
    
    # 3-Jahres-Nutzen
    total_benefit_3years = 0
    for year in range(1, years + 1):
        year_benefit = sum(b.amount * b.probability for b in benefits if b.year <= year)
        year_cost = recurring_costs
        net_benefit = year_benefit - year_cost
        # Diskontieren
        discounted = net_benefit / ((1 + discount_rate) ** year)
        total_benefit_3years += discounted
    
    # ROI berechnen
    net_gain = total_benefit_3years - total_investment
    roi_percent = (net_gain / total_investment * 100) if total_investment > 0 else 0
    
    # Payback Period
    monthly_benefit = benefit_year1 / 12
    payback_months = total_investment / monthly_benefit if monthly_benefit > 0 else 999
    
    # NPV
    npv = -total_investment
    for year in range(1, years + 1):
        year_benefit = sum(b.amount * b.probability for b in benefits if b.year <= year)
        year_cost = recurring_costs
        cash_flow = year_benefit - year_cost
        npv += cash_flow / ((1 + discount_rate) ** year)
    
    # IRR (vereinfacht)
    irr = roi_percent / years / 100 if years > 0 else 0
    
    # Break-even
    break_even = int(payback_months) + 1 if payback_months < 999 else 36
    
    # Confidence Level
    if roi_percent > 100 and payback_months < 18:
        confidence = "High"
    elif roi_percent > 50 and payback_months < 24:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return ROICalculation(
        total_investment=round(total_investment, 2),
        total_benefit_year1=round(benefit_year1, 2),
        total_benefit_3years=round(total_benefit_3years, 2),
        roi_percent=round(roi_percent, 1),
        payback_months=round(payback_months, 1),
        npv=round(npv, 2),
        irr=round(irr * 100, 1),
        break_even_month=break_even,
        confidence_level=confidence
    )


# ============================================
# BUSINESS CASE GENERATION
# ============================================

def generate_business_case(
    brief: str,
    topic: str,
    industry: str = "",
    company_size: str = "Mittelstand",
    use_llm: bool = True
) -> BusinessCase:
    """
    Generiert einen vollständigen Business Case.
    
    Args:
        brief: Das Projekt-Briefing
        topic: Hauptthema
        industry: Branche
        company_size: Unternehmensgröße
        use_llm: LLM für erweiterte Analyse nutzen?
    
    Returns:
        BusinessCase-Objekt
    """
    # Projektwert schätzen
    value_estimate = estimate_project_value(brief, industry, company_size)
    estimated_value = value_estimate["estimated_value"]
    benchmark = value_estimate["benchmark"]
    
    # Kosten generieren
    impl_factor = benchmark.get("implementation_factor", 0.75)
    impl_cost = estimated_value * impl_factor
    
    costs = [
        CostItem(name="Implementierung", amount=impl_cost * 0.6, category="Implementation"),
        CostItem(name="Beratung & Training", amount=impl_cost * 0.25, category="Implementation"),
        CostItem(name="Change Management", amount=impl_cost * 0.15, category="Implementation"),
        CostItem(name="Laufende Wartung", amount=impl_cost * 0.1, category="Recurring", year=1),
    ]
    
    # Nutzen generieren
    savings_range = list(benchmark.get("typical_savings", {}).values())
    if savings_range:
        avg_saving_percent = sum(s[0] + s[1] for s in savings_range) / len(savings_range) / 2
    else:
        avg_saving_percent = 20
    
    annual_benefit = estimated_value * (avg_saving_percent / 100) * 2  # Faktor für Jahr 1
    
    benefits = [
        BenefitItem(name="Effizienzsteigerung", amount=annual_benefit * 0.4, category="Savings", probability=0.85),
        BenefitItem(name="Kosteneinsparung", amount=annual_benefit * 0.3, category="Savings", probability=0.8),
        BenefitItem(name="Produktivitätssteigerung", amount=annual_benefit * 0.2, category="Productivity", probability=0.75),
        BenefitItem(name="Risikoreduktion", amount=annual_benefit * 0.1, category="Risk", probability=0.7),
    ]
    
    # ROI berechnen
    roi = calculate_roi(costs, benefits)
    
    # Business Case erstellen
    bc = BusinessCase(
        title=f"Business Case: {topic}",
        executive_summary=f"Investition von {impl_cost:,.0f}€ mit erwartetem ROI von {roi.roi_percent:.0f}% über 3 Jahre.",
        costs=costs,
        benefits=benefits,
        roi=roi,
        assumptions=[
            f"Branchentypische Einsparungen von {avg_saving_percent:.0f}%",
            f"Implementierungsdauer von {benchmark.get('realization_time_months', 6)} Monaten",
            f"Unternehmensgröße: {company_size}",
            "Keine größeren externen Störungen"
        ],
        risks=[
            "Verzögerungen in der Implementierung",
            "Änderungen im Projektumfang",
            "Akzeptanz durch Mitarbeiter"
        ],
        recommendation="Investition empfohlen" if roi.roi_percent > 50 else "Detaillierte Analyse empfohlen"
    )
    
    # LLM-Erweiterung für Executive Summary
    if use_llm and HAS_LLM and llm_enabled and llm_enabled():
        bc = _enhance_business_case_with_llm(bc, brief, topic, industry)
    
    return bc


def _enhance_business_case_with_llm(
    bc: BusinessCase,
    brief: str,
    topic: str,
    industry: str
) -> BusinessCase:
    """Erweitert Business Case mit LLM."""
    prompt = f"""Verbessere diese Executive Summary für einen Business Case:

Thema: {topic}
Branche: {industry}
ROI: {bc.roi.roi_percent:.0f}%
Payback: {bc.roi.payback_months:.0f} Monate
Investition: {bc.roi.total_investment:,.0f}€

Aktuelle Summary: {bc.executive_summary}

Generiere eine überzeugende, professionelle Executive Summary (2-3 Sätze).

Antworte NUR mit dem Text der Summary, keine JSON."""

    try:
        result = llm_generate(prompt, max_tokens=150)
        if result.get("ok"):
            response = result.get("response", "").strip()
            if len(response) > 50:
                bc.executive_summary = response
    except Exception:
        pass
    
    return bc


# ============================================
# SLIDE CONTENT GENERATION
# ============================================

def roi_to_slide_content(roi: ROICalculation, title: str = "ROI & Business Case") -> Dict[str, Any]:
    """Konvertiert ROI zu Slide-Content."""
    return {
        "type": "roi",
        "title": title,
        "bullets": [
            f"Gesamtinvestition: {roi.total_investment:,.0f}€",
            f"ROI nach 3 Jahren: {roi.roi_percent:.0f}%",
            f"Amortisation: {roi.payback_months:.0f} Monate",
            f"Jährlicher Nutzen: {roi.total_benefit_year1:,.0f}€",
            f"NPV: {roi.npv:,.0f}€"
        ],
        "notes": f"Business Case mit {roi.confidence_level} Confidence. Break-even in Monat {roi.break_even_month}.",
        "layout_hint": "Title and Content",
        "roi_data": asdict(roi),
        "chart_type": "bar",
        "chart_data": {
            "labels": ["Investition", "Nutzen Jahr 1", "Nutzen 3 Jahre", "ROI"],
            "values": [roi.total_investment, roi.total_benefit_year1, roi.total_benefit_3years, roi.roi_percent * 1000]
        }
    }


def business_case_to_slides(bc: BusinessCase) -> List[Dict[str, Any]]:
    """Konvertiert Business Case zu mehreren Slides."""
    slides = []
    
    # Executive Summary Slide
    slides.append({
        "type": "business_case_summary",
        "title": "Business Case: Executive Summary",
        "bullets": [bc.executive_summary] + bc.assumptions[:2],
        "notes": bc.recommendation,
        "layout_hint": "Title and Content"
    })
    
    # ROI Slide
    if bc.roi:
        slides.append(roi_to_slide_content(bc.roi, "ROI-Analyse"))
    
    # Kosten/Nutzen Slide
    cost_total = sum(c.amount for c in bc.costs)
    benefit_total = sum(b.amount for b in bc.benefits)
    
    slides.append({
        "type": "cost_benefit",
        "title": "Kosten-Nutzen-Übersicht",
        "bullets": [
            f"Gesamtkosten: {cost_total:,.0f}€",
            f"Gesamtnutzen (Jahr 1): {benefit_total:,.0f}€",
            f"Netto-Nutzen: {benefit_total - cost_total:,.0f}€",
        ],
        "notes": "Detaillierte Kosten-Nutzen-Analyse",
        "layout_hint": "Title and Content"
    })
    
    return slides


# ============================================
# SENSITIVITY ANALYSIS
# ============================================

def sensitivity_analysis(
    bc: BusinessCase,
    variables: List[str] = None,
    variation: float = 0.2  # ±20%
) -> Dict[str, Any]:
    """
    Führt Sensitivitätsanalyse durch.
    
    Args:
        bc: Der Business Case
        variables: Zu analysierende Variablen
        variation: Variationsbereich (default ±20%)
    
    Returns:
        Dictionary mit Szenarien
    """
    if variables is None:
        variables = ["costs", "benefits", "timeline"]
    
    scenarios = {
        "base": asdict(bc.roi) if bc.roi else {},
        "optimistic": {},
        "pessimistic": {}
    }
    
    # Optimistisch: -20% Kosten, +20% Nutzen
    opt_costs = [CostItem(**{**asdict(c), "amount": c.amount * (1 - variation)}) for c in bc.costs]
    opt_benefits = [BenefitItem(**{**asdict(b), "amount": b.amount * (1 + variation)}) for b in bc.benefits]
    opt_roi = calculate_roi(opt_costs, opt_benefits)
    scenarios["optimistic"] = asdict(opt_roi)
    
    # Pessimistisch: +20% Kosten, -20% Nutzen
    pess_costs = [CostItem(**{**asdict(c), "amount": c.amount * (1 + variation)}) for c in bc.costs]
    pess_benefits = [BenefitItem(**{**asdict(b), "amount": b.amount * (1 - variation)}) for b in bc.benefits]
    pess_roi = calculate_roi(pess_costs, pess_benefits)
    scenarios["pessimistic"] = asdict(pess_roi)
    
    return {
        "ok": True,
        "variation": variation,
        "scenarios": scenarios,
        "recommendation": "Robust" if pess_roi.roi_percent > 20 else "Risikobehaftet"
    }


# ============================================
# API FUNCTIONS
# ============================================

def calculate_project_roi(
    brief: str,
    topic: str,
    industry: str = "",
    company_size: str = "Mittelstand"
) -> Dict[str, Any]:
    """
    Hauptfunktion: Berechnet ROI für ein Projekt.
    
    Returns:
        Dictionary mit business_case, roi, slides, sensitivity
    """
    bc = generate_business_case(brief, topic, industry, company_size)
    sensitivity = sensitivity_analysis(bc)
    slides = business_case_to_slides(bc)
    
    return {
        "ok": True,
        "business_case": asdict(bc),
        "roi": asdict(bc.roi) if bc.roi else None,
        "sensitivity": sensitivity,
        "slides": slides,
        "recommendation": bc.recommendation
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status des ROI Calculators zurück."""
    return {
        "ok": True,
        "industries_supported": len(INDUSTRY_BENCHMARKS),
        "llm_available": HAS_LLM and (llm_enabled() if llm_enabled else False),
        "features": ["roi_calculation", "business_case", "sensitivity_analysis", "slide_generation"]
    }
