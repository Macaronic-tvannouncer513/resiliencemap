# ResilienceMap Risk Scoring Methodology

**Version:** 0.1  
**Author:** Henok Haile  
**Date:** 2025

---

## Overview

ResilienceMap computes a composite disaster risk score for each US Census tract
using publicly available federal datasets. Scores range from 0.0 (minimal risk)
to 1.0 (maximum risk) and are intended to support municipal emergency planning,
resource prioritization, and public awareness.

This document describes data sources, score components, weighting rationale,
and known limitations.

---

## Data Sources

| Component | Source | Dataset | Update Frequency |
|-----------|--------|---------|-----------------|
| Flood risk | FEMA | National Flood Hazard Layer (NFHL) — S_FLD_HAZ_AR | Annually |
| Seismic risk | USGS | FDSN Earthquake Event Service | Real-time |
| Storm exposure | NOAA NWS | Weather Alert API (CAP/ATOM) | Hourly |
| Social vulnerability | CDC/ATSDR | Social Vulnerability Index (SVI) | Every 2 years |
| Tract boundaries | US Census | TIGER/Line Shapefiles | Annually |

All datasets are in the public domain and freely accessible without licensing restrictions.

---

## Score Components

### 1. Flood Risk Score (weight: 35%)

**Methodology:** For each census tract, we compute the fraction of its land area that intersects FEMA-designated Special Flood Hazard Areas (SFHAs). SFHAs are areas with a ≥1% annual chance of flooding (commonly referred to as the "100-year floodplain").

```
flood_score = ST_Area(tract ∩ SFHA) / ST_Area(tract)
```

**Zone classification:**
- High risk (SFHA): Zone A, AE, AH, AO, AR, A99, V, VE
- Moderate risk: Zone B, X
- Undetermined: Zone D

**Rationale:** Flood damage is the most costly natural disaster type in the US (FEMA, 2023). NFHL is the authoritative federal dataset for flood risk. Area-weighted intersection is a standard spatial analysis technique in emergency management literature.

---

### 2. Seismic Risk Score (weight: 25%)

**Methodology:** For each tract centroid, we compute a magnitude-weighted proximity score for all earthquakes within 500 km in the past 365 days:

```
raw_seismic = Σ (magnitude² / max(distance_km, 1))
seismic_score = min(raw_seismic / 200.0, 1.0)
```

Squaring the magnitude reflects the exponential energy release relationship (Gutenberg-Richter). The normalization constant (200.0) was calibrated against historical high-seismicity regions (Los Angeles Basin, Pacific Northwest, New Madrid Seismic Zone).

**Rationale:** USGS provides real-time, free earthquake data via FDSN. Magnitude-distance decay is consistent with ground motion prediction equation (GMPE) literature.

---

### 3. Storm Exposure Score (weight: 25%)

**Methodology:** For each active NOAA NWS warning or watch whose polygon intersects a tract:

```
severity_weight: Extreme=1.0, Severe=0.75, Moderate=0.50, Minor=0.25
storm_score = min(Σ severity_weights / 4.0, 1.0)
```

The denominator (4.0) represents simultaneous severe alerts from four different hazard types, representing a practically maximal storm exposure scenario.

**Rationale:** NOAA CAP (Common Alerting Protocol) messages are the standard format for official US weather alerts. Severity tiers align with NWS operational definitions.

---

### 4. Social Vulnerability Score (weight: 15%)

**Methodology:** The CDC/ATSDR Social Vulnerability Index (SVI) for each tract is used directly as the component score. SVI is a 0–1 composite of:
- Socioeconomic status (income, poverty, employment)
- Household composition (elderly, disabled, single-parent)
- Minority status and language
- Housing type and transportation access

**Rationale:** Social vulnerability amplifies physical hazard impacts. Lower-income and minority communities consistently face disproportionate disaster impacts (Cutter et al., 2003; Fothergill & Peek, 2004). Incorporating SVI aligns ResilienceMap with FEMA's equity-centered approach to resilience planning.

---

## Composite Score

The weighted composite is:

```
composite = 0.35 × flood + 0.25 × seismic + 0.25 × storm + 0.15 × svi
```

**Weight justification:**
- Flood (35%) is the most consistently costly and geographically pervasive US hazard
- Seismic and Storm (25% each) are regionally dominant and data-rich
- SVI (15%) modifies physical risk without overriding it — a vulnerability modifier

Weights are configurable and can be adjusted by practitioners for regional contexts.

---

## Limitations and Future Work

1. **NFHL coverage gaps:** FEMA's NFHL does not cover all US parcels. Unmapped areas default to 0.0 flood score, which may understate risk in rural areas.

2. **Seismic hazard lookback:** The 365-day window captures recent activity but may miss long-recurrence faults. Future work: integrate USGS National Seismic Hazard Model static layers.

3. **Storm score temporality:** Storm alerts expire quickly. The score reflects current exposure, not historical storm climatology. Future work: integrate NOAA storm event historical data.

4. **SVI data lag:** SVI is published on Census years (2010, 2014, 2016, 2018, 2020, 2022). Between releases, vulnerability patterns may shift significantly.

5. **Model validation:** This scoring model has not been formally validated against observed disaster impacts. Future work: compare composite scores against FEMA disaster declaration data and SHELDUS economic loss data.

---

## References

- Cutter, S.L., Boruff, B.J., & Shirley, W.L. (2003). Social vulnerability to environmental hazards. *Social Science Quarterly*, 84(2), 242–261.
- FEMA (2023). *National Flood Insurance Program: Flood Insurance Claims Data*. Federal Emergency Management Agency.
- Fothergill, A., & Peek, L. (2004). Poverty and disasters in the United States: A review of recent sociological findings. *Natural Hazards*, 32(1), 89–110.
- USGS (2024). *USGS Earthquake Hazards Program: FDSN Web Services*. United States Geological Survey.
