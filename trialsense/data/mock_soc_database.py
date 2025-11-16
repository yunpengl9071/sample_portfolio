"""
Mock Standard of Care (SOC) Database

⚠️ TODO: Replace with real data sources
This is a TEMPORARY mock database for demonstrating the SOC alignment feature.

In production, this should be replaced with:
- Vector store of clinical guidelines (NCCN, ESMO, ASCO)
- FDA/EMA drug approval databases
- Real-time guideline updates
- LLM-based guideline interpretation

Current limitations:
- Only covers top 10 conditions
- Static data (not updated)
- Simplified country coverage (US, EU, JP)
- Missing nuances (line of therapy, specific histologies)
"""

from typing import Dict, List, Optional


# Mock SOC database structure
# {condition: {country: {line: recommended_treatments}}}
MOCK_SOC_DATABASE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "Non-Small Cell Lung Cancer": {
        "US": {
            "first_line": [
                "Pembrolizumab + Platinum-based chemotherapy",
                "Atezolizumab + Bevacizumab + Carboplatin + Paclitaxel",
                "Nivolumab + Ipilimumab",
            ],
            "second_line": [
                "Docetaxel",
                "Pemetrexed",
                "Nivolumab",
                "Pembrolizumab",
            ],
        },
        "EU": {
            "first_line": [
                "Platinum doublet chemotherapy",
                "Pembrolizumab + chemotherapy (PD-L1 ≥1%)",
            ],
            "second_line": [
                "Docetaxel",
                "Pemetrexed",
                "Nivolumab",
            ],
        },
        "JP": {
            "first_line": [
                "Platinum-based chemotherapy",
                "Carboplatin + Paclitaxel",
            ],
            "second_line": [
                "Docetaxel",
                "Pemetrexed",
            ],
        },
    },
    "Breast Cancer": {
        "US": {
            "adjuvant": [
                "Anthracycline + Cyclophosphamide followed by Taxane",
                "Docetaxel + Cyclophosphamide",
                "Trastuzumab (HER2+)",
            ],
            "metastatic_her2_positive": [
                "Trastuzumab + Pertuzumab + Taxane",
                "T-DM1",
            ],
            "metastatic_her2_negative": [
                "CDK4/6 inhibitor + Aromatase inhibitor (HR+)",
                "Chemotherapy (triple negative)",
            ],
        },
        "EU": {
            "adjuvant": [
                "Anthracycline-based regimen",
                "FEC (5-FU + Epirubicin + Cyclophosphamide)",
            ],
            "metastatic_her2_positive": [
                "Trastuzumab + Taxane",
                "Pertuzumab + Trastuzumab + Docetaxel",
            ],
        },
        "JP": {
            "adjuvant": [
                "Anthracycline + Taxane",
            ],
            "metastatic_her2_positive": [
                "Trastuzumab + Chemotherapy",
            ],
        },
    },
    "Melanoma": {
        "US": {
            "adjuvant": [
                "Nivolumab",
                "Pembrolizumab",
                "Dabrafenib + Trametinib (BRAF V600+)",
            ],
            "metastatic_braf_mutant": [
                "Dabrafenib + Trametinib",
                "Vemurafenib + Cobimetinib",
                "Encorafenib + Binimetinib",
            ],
            "metastatic_braf_wild_type": [
                "Nivolumab + Ipilimumab",
                "Pembrolizumab",
                "Nivolumab",
            ],
        },
        "EU": {
            "adjuvant": [
                "Nivolumab",
                "Pembrolizumab",
            ],
            "metastatic": [
                "Nivolumab + Ipilimumab",
                "Pembrolizumab",
                "BRAF/MEK inhibitors (BRAF mutant)",
            ],
        },
        "JP": {
            "adjuvant": [
                "Nivolumab",
            ],
            "metastatic": [
                "Nivolumab",
                "Pembrolizumab",
            ],
        },
    },
    "Colorectal Cancer": {
        "US": {
            "adjuvant": [
                "FOLFOX (5-FU + Leucovorin + Oxaliplatin)",
                "CAPOX (Capecitabine + Oxaliplatin)",
            ],
            "metastatic_first_line": [
                "FOLFOX or FOLFIRI + Bevacizumab",
                "FOLFOX or FOLFIRI + Cetuximab (KRAS wild-type)",
            ],
            "metastatic_second_line": [
                "FOLFIRI + Aflibercept",
                "Regorafenib",
                "TAS-102",
            ],
        },
        "EU": {
            "adjuvant": [
                "FOLFOX",
                "5-FU + Leucovorin",
            ],
            "metastatic": [
                "FOLFOX + Bevacizumab",
                "FOLFIRI + Bevacizumab",
            ],
        },
        "JP": {
            "adjuvant": [
                "5-FU + Leucovorin",
            ],
            "metastatic": [
                "FOLFOX",
                "FOLFIRI",
            ],
        },
    },
    "Prostate Cancer": {
        "US": {
            "hormone_sensitive": [
                "Androgen deprivation therapy (ADT)",
                "Docetaxel + ADT",
                "Abiraterone + Prednisone + ADT",
            ],
            "castration_resistant": [
                "Enzalutamide",
                "Abiraterone + Prednisone",
                "Docetaxel",
                "Cabazitaxel",
            ],
        },
        "EU": {
            "hormone_sensitive": [
                "ADT",
                "Docetaxel + ADT (high-risk)",
            ],
            "castration_resistant": [
                "Abiraterone + Prednisone",
                "Enzalutamide",
                "Docetaxel",
            ],
        },
        "JP": {
            "hormone_sensitive": [
                "ADT",
            ],
            "castration_resistant": [
                "Abiraterone",
                "Enzalutamide",
                "Docetaxel",
            ],
        },
    },
    # TODO: Add more conditions
    # - Ovarian Cancer
    # - Pancreatic Cancer
    # - Multiple Myeloma
    # - Non-Hodgkin Lymphoma
    # - Chronic Lymphocytic Leukemia
    # - Acute Myeloid Leukemia
    # - Renal Cell Carcinoma
    # - Hepatocellular Carcinoma
    # - Glioblastoma
    # - Heart Failure
    # - Atrial Fibrillation
    # - Diabetes Type 2
    # - Alzheimer's Disease
    # - Parkinson's Disease
}


def get_soc(
    condition: str,
    country: str = "US",
    line_of_therapy: Optional[str] = None
) -> List[str]:
    """
    Get standard of care for a condition in a country.

    Args:
        condition: Disease/condition name
        country: Country code (US, EU, JP, etc.)
        line_of_therapy: Specific line/setting (e.g., "first_line", "adjuvant")

    Returns:
        List of recommended treatments (empty if not found)

    Example:
        >>> get_soc("Non-Small Cell Lung Cancer", "US", "first_line")
        ['Pembrolizumab + Platinum-based chemotherapy', ...]
    """
    # Normalize condition name
    condition_normalized = condition.strip()

    # Check if condition in database
    if condition_normalized not in MOCK_SOC_DATABASE:
        # Try partial match
        for key in MOCK_SOC_DATABASE.keys():
            if condition_normalized.lower() in key.lower() or key.lower() in condition_normalized.lower():
                condition_normalized = key
                break
        else:
            return []  # Condition not found

    country_data = MOCK_SOC_DATABASE[condition_normalized].get(country, {})

    if not country_data:
        return []  # Country not found

    # If line of therapy specified, return that
    if line_of_therapy:
        return country_data.get(line_of_therapy, [])

    # Otherwise return all lines combined
    all_treatments = []
    for treatments in country_data.values():
        all_treatments.extend(treatments)

    return all_treatments


def check_soc_alignment(
    condition: str,
    control_arm: str,
    country: str = "US"
) -> float:
    """
    Check if control arm matches standard of care.

    Args:
        condition: Disease/condition name
        control_arm: Control arm treatment name
        country: Country code

    Returns:
        Alignment score (0.0 - 1.0)
        - 1.0 = perfect match
        - 0.5 = partial match (similar but not exact)
        - 0.0 = no match

    Example:
        >>> check_soc_alignment("NSCLC", "Pembrolizumab + Carboplatin", "US")
        1.0  # Perfect match

        >>> check_soc_alignment("NSCLC", "Docetaxel", "US")
        0.5  # Partial match (second-line SOC)

        >>> check_soc_alignment("NSCLC", "Placebo", "US")
        0.0  # No match
    """
    soc_treatments = get_soc(condition, country)

    if not soc_treatments:
        return 0.5  # Unknown → neutral score

    control_lower = control_arm.lower()

    # Check for perfect match
    for soc_treatment in soc_treatments:
        if soc_treatment.lower() in control_lower or control_lower in soc_treatment.lower():
            return 1.0  # Perfect match

    # Check for partial match (contains any component)
    for soc_treatment in soc_treatments:
        soc_components = [comp.strip() for comp in soc_treatment.lower().split("+")]
        control_components = [comp.strip() for comp in control_lower.split("+")]

        # If any component matches
        if any(
            soc_comp in control_comp or control_comp in soc_comp
            for soc_comp in soc_components
            for control_comp in control_components
        ):
            return 0.6  # Partial match

    # No match
    return 0.0


def get_supported_conditions() -> List[str]:
    """Get list of conditions in the mock database."""
    return list(MOCK_SOC_DATABASE.keys())


def get_supported_countries() -> List[str]:
    """Get list of countries in the mock database."""
    return ["US", "EU", "JP"]


# Example usage and testing
if __name__ == "__main__":
    # Test get_soc
    print("=== Testing get_soc ===")
    print("\nNSCLC first-line in US:")
    print(get_soc("Non-Small Cell Lung Cancer", "US", "first_line"))

    print("\nBreast cancer HER2+ metastatic in EU:")
    print(get_soc("Breast Cancer", "EU", "metastatic_her2_positive"))

    # Test check_soc_alignment
    print("\n\n=== Testing check_soc_alignment ===")

    test_cases = [
        ("Non-Small Cell Lung Cancer", "Pembrolizumab + Carboplatin", "US"),
        ("Non-Small Cell Lung Cancer", "Docetaxel", "US"),
        ("Non-Small Cell Lung Cancer", "Placebo", "US"),
        ("Breast Cancer", "Trastuzumab + Pertuzumab + Docetaxel", "US"),
        ("Melanoma", "Nivolumab", "JP"),
    ]

    for condition, control, country in test_cases:
        score = check_soc_alignment(condition, control, country)
        print(f"\n{condition} | {control} | {country}")
        print(f"  Alignment: {score:.1f} ({'✓' if score >= 0.6 else '✗'})")

    # List supported conditions
    print("\n\n=== Supported Conditions ===")
    for condition in get_supported_conditions():
        print(f"- {condition}")

    print("\n⚠️ NOTE: This is mock data. In production, use real guideline databases.")
