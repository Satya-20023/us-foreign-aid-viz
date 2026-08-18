# Visualizing US Foreign Aid: Trends, Allocation, and Impact

Interactive Plotly dashboard plus a D3.js choropleth over 2001–2024 U.S. foreign aid (bundled sample of 1,000+ records).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python generate_data.py
streamlit run app.py
```

The choropleth lives at `choropleth.html` — open it in a browser after generating data (it reads `data/aid_by_country.json`).
