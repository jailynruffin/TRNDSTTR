# ⭐ TRNDSTTR

Media & culture trend intelligence for creators and marketers.  
Fetch Google Trends data, analyze top movers, and export insights — all in a clean, modern Streamlit dashboard.

---

##  Features

- **Google Trends Fetching**  
  Track up to 5 keywords at a time (cached for 1 hour with rate-limit handling).
- **Key Metrics**  
  Quick glance at keywords tracked, total interest, and the current top mover.
- **Top Movers**  
  Compare last 7 days vs. the previous 7, with an interactive bar chart + linked timeseries.
- **Timeseries Explorer**  
  See historical interest across multiple timeframes (7d, 3m, 12m, 5y).
- **Data Export**  
  One-click CSV or Excel download of both KPIs and full timeseries.
- **SQLite Persistence**  
  Fetched data is stored locally for re-use and snapshotting.

---

##  Screenshots

- **Landing Page**  
  <img width="1895" height="901" alt="image" src="https://github.com/user-attachments/assets/6c8e0952-8fba-46d4-b211-3a3d9a305a48" />

- **Key Metrics**  
  <img width="1056" height="214" alt="image" src="https://github.com/user-attachments/assets/ce15b27f-e900-49b4-bca1-21eef2edae5b" />

- **Top Movers**  
  <img width="1107" height="825" alt="image" src="https://github.com/user-attachments/assets/15bfab6e-c0ff-402d-a215-4121a47f0a46" />

- **Timeseries**  
  <img width="981" height="445" alt="image" src="https://github.com/user-attachments/assets/fa4816c8-94a8-4ac3-90f6-efa2ffefe1f7" />


---

##  Try It

- Live demo: [COMING SOON]
- Local run:
  bash
- git clone https://github.com/<jailynruffin>/trndsttr.git
- cd trndsttr
- pip install -r requirements.txt
- streamlit run streamlit_app.py
