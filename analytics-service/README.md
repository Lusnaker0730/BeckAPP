# FHIR Analytics Service

Advanced analytics and data science service for FHIR data.

## Features

- 📊 **Data Visualization**
  - Configurable X/Y axis
  - Multiple chart types
  - Real-time data aggregation

- 📈 **Statistical Analysis**
  - Descriptive statistics
  - Correlation analysis
  - Trend analysis
  - Time series forecasting

- 👥 **Cohort Analysis**
  - Define patient cohorts
  - Compare cohorts
  - Survival analysis (Kaplan-Meier)
  - Risk stratification

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

```env
DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/fhir_analytics
```

## Usage

```bash
uvicorn main:app --port 8002 --reload
```

## API Endpoints

### Visualization

**Get Visualization Data**
```bash
GET /api/visualization?xAxis=age_group&yAxis=count&filter=all
```

### Statistics

**Descriptive Statistics**
```bash
GET /api/statistics/descriptive?resource_type=conditions
```

**Correlation Analysis**
```bash
GET /api/statistics/correlation?variable1=age&variable2=condition_count
```

**Trend Analysis**
```bash
GET /api/statistics/trend-analysis?metric=condition_count&time_period=monthly
```

### Cohort Analysis

**Define Cohort**
```bash
POST /api/cohort/define
{
  "name": "Diabetes Patients",
  "inclusion_criteria": {
    "condition": "diabetes",
    "age_min": 18,
    "age_max": 65
  }
}
```

**Compare Cohorts**
```bash
GET /api/cohort/compare?cohort1_criteria=...&cohort2_criteria=...
```

**Survival Analysis**
```bash
GET /api/cohort/survival-analysis?cohort_criteria=...&event=...&follow_up_months=12
```

## Supported Analyses

### Descriptive Statistics
- Count, mean, median, mode
- Standard deviation, variance
- Min, max, range
- Percentiles

### Correlation Analysis
- Pearson correlation
- Spearman correlation
- Point-biserial correlation

### Trend Analysis
- Linear regression
- Moving averages
- Seasonal decomposition
- Forecasting (ARIMA)

### Cohort Analysis
- Inclusion/exclusion criteria
- Cohort comparison
- Kaplan-Meier survival curves
- Cox proportional hazards
- Log-rank test

## Data Aggregation

Supports multiple aggregation levels:
- Daily
- Weekly
- Monthly
- Quarterly
- Yearly

## Visualization Variables

### X-Axis Options
- age_group
- gender
- condition_code
- encounter_type
- date
- location

### Y-Axis Options
- count (frequency)
- average (mean value)
- total (sum)
- percentage
- rate

## Statistical Tests

- T-test
- Chi-square test
- ANOVA
- Mann-Whitney U test
- Kruskal-Wallis test

## Machine Learning (Future)

- Predictive modeling
- Risk scoring
- Patient clustering
- Anomaly detection

## Performance

- Optimized SQL queries
- Query result caching
- Parallel processing
- Batch computations

## License

MIT

