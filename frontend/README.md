# FHIR Analytics Platform - Frontend

React-based frontend application with SMART on FHIR integration.

## Features

- 🔐 **Authentication**
  - Standalone Login
  - SMART on FHIR EHR Launch
  - JWT Token Management

- 📊 **Dashboard**
  - Real-time Statistics
  - Trend Analysis
  - Top Diagnoses

- 🏥 **Diagnosis Analysis**
  - Annual Incidence Analysis
  - Filter by Diagnosis Type
  - Time Range Selection
  - Interactive Charts

- 📈 **Data Visualization**
  - Configurable X/Y Axis
  - Multiple Chart Types (Bar, Line, Scatter, Pie)
  - Export Charts as Images

- 💾 **Data Export**
  - Multiple Format Support (CSV, JSON, Excel, Parquet)
  - Custom Field Selection
  - Date Range Filtering

- ⚙️ **Admin Panel** (Engineers Only)
  - BULK DATA API Configuration
  - ETL Job Management
  - Valuesets Management
  - API Endpoint Configuration

## Tech Stack

- **React** 18.2
- **React Router** 6.20
- **Chart.js** 4.4 & React-Chartjs-2
- **FHIR Client** 2.5.2
- **Axios** for API calls
- **Papa Parse** for CSV handling

## Installation

```bash
npm install
```

## Environment Variables

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ANALYTICS_URL=http://localhost:8002
REACT_APP_FHIR_CLIENT_ID=your-fhir-client-id
REACT_APP_FHIR_REDIRECT_URI=http://localhost:3000/callback
REACT_APP_FHIR_SCOPE=patient/*.read launch/patient openid fhirUser
```

## Development

```bash
npm start
```

Runs on http://localhost:3000

## Build

```bash
npm run build
```

## SMART on FHIR Integration

The application supports SMART on FHIR launch flow:

1. **Standalone Launch**: Users can manually connect to a FHIR server
2. **EHR Launch**: Launch from within an EHR system using the `/launch.html` endpoint

### Launch Flow

1. EHR initiates launch with `iss` and `launch` parameters
2. App redirects to authorization server
3. User authorizes access
4. App receives authorization code
5. App exchanges code for access token
6. App accesses FHIR resources

## Project Structure

```
src/
├── components/
│   ├── Auth/              # Authentication components
│   ├── Dashboard/         # Dashboard components
│   ├── Analysis/          # Diagnosis analysis
│   ├── Visualization/     # Data visualization
│   ├── Export/            # Data export
│   ├── Admin/             # Admin panel
│   └── Layout/            # Layout components
├── App.js
├── App.css
├── index.js
└── index.css
```

## Security

- JWT-based authentication
- OAuth 2.0 / SMART on FHIR
- Token storage in localStorage
- Protected routes with PrivateRoute component
- CORS configuration for API calls

## License

MIT

