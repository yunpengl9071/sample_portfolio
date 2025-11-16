# Treatment Landscape Agent - Design Document

## 🎯 Overview

The **Treatment Landscape Agent** assesses whether a trial's control arm treatment aligns with the standard of care (SOC) in planned trial countries. This is a critical feature for predicting trial success because:

1. **Regulatory Approval**: Trials using non-SOC comparators may face regulatory challenges
2. **Recruitment**: Sites may be reluctant to enroll if control isn't SOC
3. **Ethics**: IRBs scrutinize trials where control doesn't match local SOC
4. **Publication**: Non-SOC comparators reduce publication likelihood

---

## 🔧 Core Functionality

### **Input**
- Trial condition/disease
- Control arm intervention(s)
- Planned trial countries/regions
- Trial phase

### **Output**
- SOC alignment score (0.0 - 1.0 per country)
- Mismatch warnings
- Recommended alternatives
- Risk assessment

---

## 🏗️ Architecture

```
Treatment Landscape Agent
├── SOC Knowledge Base (Vector Store)
│   ├── Clinical guidelines (NCCN, ASCO, ESMO, etc.)
│   ├── Country-specific formularies
│   ├── Historical trial controls
│   └── Drug approval databases (FDA, EMA, PMDA)
│
├── LLM Reasoning Engine
│   ├── Guideline interpretation
│   ├── Multi-country comparison
│   └── Risk assessment
│
└── Tools
    ├── GuidelineLookupTool
    ├── DrugApprovalTool
    ├── HistoricalTrialTool
    └── CountryFormularyTool
```

---

## 📊 Feature Engineering

### **New Feature: `control_soc_alignment`**

Numeric score (0.0 - 1.0) indicating how well control arm matches SOC across all planned countries.

```python
control_soc_alignment = (
    sum(country_soc_scores) / num_countries
)
```

**Example:**
- US: 1.0 (perfect match)
- EU: 0.8 (mostly matches, minor differences)
- Japan: 0.6 (partial match, some guidelines differ)
- **Overall: 0.8** (80% alignment)

### **Impact on Prediction**

This feature would be added to the XGBoost model:

```python
features = {
    # ... existing 17 features ...
    "control_soc_alignment": 0.8,  # NEW feature
}
```

**Expected correlation:**
- Higher SOC alignment → Higher success probability
- Low SOC alignment (<0.5) → Red flag for regulatory/recruitment

---

## 🔍 Agent Implementation

### **File: `trialsense/agents/treatment_landscape_agent.py`**

```python
from typing import List, Dict, Any
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

from trialsense.agents.base import BaseAgent
from trialsense.tools.treatment_landscape_tools import (
    GuidelineLookupTool,
    DrugApprovalTool,
)


class TreatmentLandscapeAgent(BaseAgent):
    """
    Agent that assesses standard of care alignment for trial control arms.

    Uses clinical guidelines, drug approvals, and historical data to determine
    if the control arm treatment matches standard of care in planned countries.
    """

    def __init__(self, llm: ChatOpenAI):
        tools = [
            GuidelineLookupTool(),
            DrugApprovalTool(),
        ]

        super().__init__(
            name="TreatmentLandscapeAgent",
            description="Assesses standard of care alignment for trial control arms",
            llm=llm,
            tools=tools,
        )

    def assess_soc_alignment(
        self,
        condition: str,
        control_interventions: List[str],
        countries: List[str],
        phase: str,
    ) -> Dict[str, Any]:
        """
        Assess standard of care alignment.

        Args:
            condition: Disease/condition being studied
            control_interventions: List of control arm treatments
            countries: List of trial countries
            phase: Trial phase

        Returns:
            Dictionary with:
            - overall_alignment: Float 0.0-1.0
            - country_scores: Dict[country, score]
            - mismatches: List of identified mismatches
            - recommendations: List of recommended alternatives
            - risk_level: "low" | "medium" | "high"
        """
        # Build prompt for LLM
        prompt = self._build_soc_prompt(
            condition, control_interventions, countries, phase
        )

        # Run agent with tools
        result = self.run(prompt)

        # Parse result
        return self._parse_soc_result(result, countries)

    def _build_soc_prompt(
        self,
        condition: str,
        control_interventions: List[str],
        countries: List[str],
        phase: str,
    ) -> str:
        """Build prompt for SOC assessment."""
        control_str = ", ".join(control_interventions)
        countries_str = ", ".join(countries)

        return f"""
Assess whether the following control arm treatment matches standard of care
for {condition} in these countries: {countries_str}.

Control Arm: {control_str}
Trial Phase: {phase}

For each country, determine:
1. What is the current standard of care for {condition}?
2. Is {control_str} an approved and recommended treatment?
3. Does it match first-line or second-line therapy?
4. Are there any country-specific guideline differences?

Use the available tools to:
- Look up clinical guidelines (NCCN, ESMO, local guidelines)
- Check drug approval status in each country
- Find similar trials that used this control

Provide:
1. Overall alignment score (0.0 = complete mismatch, 1.0 = perfect match)
2. Country-specific scores
3. Any mismatches or concerns
4. Recommended alternatives if alignment is low
"""

    def _parse_soc_result(
        self, result: str, countries: List[str]
    ) -> Dict[str, Any]:
        """
        Parse LLM result into structured format.

        Uses LLM to extract structured data from its own response.
        """
        # Use LLM to extract structured data
        extraction_prompt = f"""
        From the following analysis, extract structured data:

        {result}

        Return JSON with:
        {{
            "overall_alignment": <float 0.0-1.0>,
            "country_scores": {{<country>: <score>, ...}},
            "mismatches": [<list of strings>],
            "recommendations": [<list of strings>],
            "risk_level": "low" | "medium" | "high"
        }}
        """

        # Get structured response (implementation would use LLM)
        # For now, return template
        return {
            "overall_alignment": 0.8,
            "country_scores": {country: 0.8 for country in countries},
            "mismatches": [],
            "recommendations": [],
            "risk_level": "low",
        }
```

---

## 🛠️ Tools

### **1. GuidelineLookupTool**

Searches clinical guidelines for standard of care.

```python
class GuidelineLookupTool(BaseTool):
    """
    Tool to search clinical guidelines.

    Sources:
    - NCCN Guidelines (US)
    - ESMO Guidelines (Europe)
    - ASCO Guidelines (International)
    - Country-specific guidelines (NICE, IQWiG, etc.)
    """

    name = "guideline_lookup"
    description = (
        "Search clinical guidelines for standard of care recommendations. "
        "Input: condition and country. "
        "Output: recommended treatments."
    )

    def _run(self, condition: str, country: str = "US") -> str:
        """
        Look up SOC in guidelines.

        In production, this would:
        1. Query guideline vector store
        2. Retrieve relevant sections
        3. Extract treatment recommendations

        For MVP, use predefined mappings or web scraping.
        """
        # Placeholder implementation
        guidelines = {
            "NSCLC": {
                "US": "Platinum-based chemotherapy + PD-L1 inhibitor",
                "EU": "Platinum doublet chemotherapy",
                "JP": "Platinum-based chemotherapy",
            },
            "Breast Cancer": {
                "US": "Anthracycline + taxane",
                "EU": "Anthracycline-based regimen",
            },
        }

        result = guidelines.get(condition, {}).get(country, "Unknown")
        return f"Standard of care for {condition} in {country}: {result}"
```

### **2. DrugApprovalTool**

Checks if drug is approved in specific countries.

```python
class DrugApprovalTool(BaseTool):
    """
    Tool to check drug approval status.

    Data sources:
    - FDA Orange Book (US)
    - EMA database (Europe)
    - PMDA (Japan)
    - Drugs@FDA API
    """

    name = "drug_approval"
    description = (
        "Check if a drug is approved in specific countries. "
        "Input: drug name and country. "
        "Output: approval status and indications."
    )

    def _run(self, drug_name: str, country: str = "US") -> str:
        """
        Check drug approval.

        In production:
        1. Query FDA/EMA/PMDA APIs
        2. Check approval status
        3. Get approved indications
        """
        # Placeholder
        return f"{drug_name} approval in {country}: Checking..."
```

### **3. HistoricalTrialTool**

Finds similar trials and their control arms.

```python
class HistoricalTrialTool(BaseTool):
    """
    Tool to find historical trials with similar conditions.

    Uses ClinicalTrials.gov data to see what controls were used
    in successful past trials.
    """

    name = "historical_trials"
    description = (
        "Find historical trials for a condition and see what "
        "control arms were used. Input: condition and phase."
    )

    def _run(self, condition: str, phase: str = "PHASE_3") -> str:
        """Search historical trials."""
        # Would query ClinicalTrials.gov or vector store
        return f"Historical trials for {condition} typically used: ..."
```

---

## 🔗 Integration with Orchestrator

### **Updated Orchestrator Workflow**

```python
class TrialSenseOrchestrator:
    def __init__(self):
        self.outcome_agent = OutcomePredictionAgent(llm)
        self.site_agent = SiteMatchingAgent(llm)
        self.treatment_agent = TreatmentLandscapeAgent(llm)  # NEW

    def _build_workflow(self):
        workflow = StateGraph(TrialAnalysisState)

        # Add nodes
        workflow.add_node("router", self._route_query)
        workflow.add_node("outcome_predictor", self._predict_outcome)
        workflow.add_node("site_matcher", self._match_sites)
        workflow.add_node("treatment_landscape", self._assess_treatment)  # NEW

        # Add edges
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "outcome": "treatment_landscape",  # NEW: Check SOC first
                "site": "site_matcher",
            }
        )

        # NEW: After SOC assessment, proceed to prediction
        workflow.add_edge("treatment_landscape", "outcome_predictor")

    def _assess_treatment(self, state: TrialAnalysisState) -> TrialAnalysisState:
        """Assess standard of care alignment."""
        trial_data = state["trial_data"]

        # Extract relevant info
        condition = trial_data.get("conditions", [{}])[0].get("name")
        control_interventions = [
            i["name"] for i in trial_data.get("interventions", [])
            if "placebo" not in i["name"].lower()
        ]
        countries = list(set([
            loc.get("country") for loc in trial_data.get("locations", [])
        ]))

        # Run treatment landscape agent
        soc_result = self.treatment_agent.assess_soc_alignment(
            condition=condition,
            control_interventions=control_interventions,
            countries=countries,
            phase=trial_data.get("phase"),
        )

        # Add to state
        state["soc_alignment"] = soc_result["overall_alignment"]
        state["soc_analysis"] = soc_result

        return state
```

---

## 📈 Impact on Predictions

### **Before Treatment Landscape Agent:**

```
Trial: Phase 3 NSCLC, Control = Docetaxel

Features:
- phase_numeric: 4
- enrollment: 340
- is_randomized: 1
- ...

Prediction: 67% success probability
```

### **After Treatment Landscape Agent:**

```
Trial: Phase 3 NSCLC, Control = Docetaxel
Countries: US, EU, Japan

Treatment Landscape Assessment:
- US SOC: Pembrolizumab + chemo (Docetaxel alone is NOT SOC)
- EU SOC: Platinum doublet (Docetaxel acceptable)
- JP SOC: Platinum-based (Docetaxel acceptable)
- Overall SOC Alignment: 0.6 (medium risk)

Features:
- phase_numeric: 4
- enrollment: 340
- is_randomized: 1
- control_soc_alignment: 0.6  # NEW
- ...

Prediction: 54% success probability (DOWN from 67%)

Warnings:
⚠️ Control arm doesn't match US standard of care
⚠️ Consider using pembrolizumab + chemo as control in US sites

Recommendations:
- Use SOC-aligned control in each country (may require multi-arm design)
- Restrict trial to countries where docetaxel is acceptable SOC
- Update protocol to use platinum doublet
```

---

## 🔄 Workflow: New Trial Upload with SOC Check

```
User uploads trial protocol
    ↓
Parse upload (TrialParser)
    ↓
Extract features (FeatureEngineer)
    ↓
Check for missing features → Prompt user
    ↓
Extract control arm and countries
    ↓
【NEW】 Run Treatment Landscape Agent
    ├─ Look up SOC in guidelines
    ├─ Check drug approvals
    ├─ Find historical trial controls
    └─ Calculate SOC alignment score
    ↓
Add control_soc_alignment to features
    ↓
Predict outcome with OutcomePredictor
    ↓
Return prediction + SOC analysis
```

---

## 📊 Data Sources

### **Guideline Sources (Vector Store)**
- NCCN Guidelines (updated annually)
- ESMO Clinical Practice Guidelines
- ASCO Clinical Practice Guidelines
- NICE Guidelines (UK)
- Australian Cancer Guidelines
- Japanese Society of Clinical Oncology

### **Regulatory Sources**
- FDA Approved Drugs & Indications
- EMA Medicines Database
- PMDA (Japan) Approved Drugs
- Health Canada Drug Database

### **Historical Data**
- ClinicalTrials.gov completed trials
- Published trial protocols
- Cochrane systematic reviews

---

## 🚀 Implementation Phases

### **Phase 1: MVP (Manual Lookup)**
- Hardcoded SOC mappings for top 10 conditions
- Simple country-level scoring
- Integration into orchestrator

### **Phase 2: Semi-Automated**
- Vector store of guidelines (PDF embeddings)
- LLM-based guideline interpretation
- FDA/EMA API integration

### **Phase 3: Fully Automated**
- Real-time guideline updates
- Multi-country regulatory tracking
- Automated alternative recommendations
- Integration with XGBoost model (retrain with new feature)

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
def test_soc_alignment_perfect_match():
    """Test when control exactly matches SOC."""
    agent = TreatmentLandscapeAgent(llm)

    result = agent.assess_soc_alignment(
        condition="NSCLC",
        control_interventions=["Pembrolizumab + Carboplatin"],
        countries=["US"],
        phase="PHASE_3",
    )

    assert result["overall_alignment"] >= 0.9
    assert result["risk_level"] == "low"


def test_soc_alignment_mismatch():
    """Test when control doesn't match SOC."""
    agent = TreatmentLandscapeAgent(llm)

    result = agent.assess_soc_alignment(
        condition="NSCLC",
        control_interventions=["Placebo"],
        countries=["US"],
        phase="PHASE_3",
    )

    assert result["overall_alignment"] < 0.5
    assert result["risk_level"] == "high"
    assert len(result["mismatches"]) > 0
```

---

## 💡 User-Facing Output

### **In Streamlit UI:**

```
Treatment Landscape Analysis
────────────────────────────────────────────────

Control Arm: Docetaxel

Standard of Care Alignment: 60% ⚠️

┌─────────────────────────────────────────────┐
│ Country-Specific Assessment                 │
├─────────────────────────────────────────────┤
│ 🇺🇸 United States         40% ⚠️           │
│   SOC: Pembrolizumab + chemo                │
│   Your control: Docetaxel (not first-line)  │
│                                             │
│ 🇪🇺 European Union        80% ✓            │
│   SOC: Platinum doublet                     │
│   Your control: Docetaxel (acceptable)      │
│                                             │
│ 🇯🇵 Japan                 70% ✓            │
│   SOC: Platinum-based                       │
│   Your control: Docetaxel (acceptable)      │
└─────────────────────────────────────────────┘

⚠️ Warnings:
• Control arm doesn't align with US standard of care
• This may impact regulatory approval and recruitment in US

💡 Recommendations:
• Consider multi-arm design with SOC control in US
• Or restrict trial to EU + Japan where alignment is good
• Or update to platinum + immunotherapy control globally

Impact on Success Probability:
Without SOC alignment feature: 67%
With SOC alignment (0.6):      54% ⬇️ -13%
```

---

## 📝 Summary

The Treatment Landscape Agent adds a critical dimension to trial outcome prediction:

✅ **Assesses control arm appropriateness**
✅ **Country-specific SOC matching**
✅ **Identifies regulatory/recruitment risks early**
✅ **Provides actionable recommendations**
✅ **Improves prediction accuracy**

**Implementation Priority:** High
**Complexity:** Medium-High
**Impact on Predictions:** High (expected +5-10% AUC improvement)

---

**Next Steps:**
1. Implement MVP with hardcoded SOC mappings
2. Integrate into orchestrator workflow
3. Add to feature engineering (control_soc_alignment feature)
4. Retrain model with new feature
5. Expand to vector store + LLM-based lookup (Phase 2)
