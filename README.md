# Opereta: Use-of-Funds Dashboard

An interactive Streamlit app to explore and stress-test the planned allocation of Opereta's pre-seed funding.

---

## 🚀 What this app does

• **Visual budgeting tool** – Adjust runway length, funding target, and optional expenses and instantly see how the budget distribution and contingency buffer change.
• **Dynamic charts** – Pie and bar charts break down spending by major categories.
• **Detailed cost tables** – Expandable sections show line-item calculations that update in real time.

The dashboard is powered by a single file, `UOF.py`, which contains a validated 15-month baseline budget (≈ $1.2 M) and the interactive Streamlit UI.

---

## 📸 Screenshot

*(Add a screenshot or GIF of the running app here)*

---

## 🛠️ Getting started locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/MJ-Ref/Use-of-Funds.git
   cd Use-of-Funds
   ```
2. **Create a virtual environment & install deps**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt  # or install streamlit + pandas + plotly directly
   ```
3. **Run the dashboard**
   ```bash
   streamlit run UOF.py
   ```
4. Visit the URL printed in the terminal (typically http://localhost:8501).

### Requirements

Minimal packages:
```txt
streamlit
pandas
plotly
```
A `requirements.txt` file is recommended so that Streamlit Cloud / other CI can install exact versions.

---

## 🔍 Repository layout

```
├── UOF.py          # Streamlit app with budgeting logic & UI
├── README.md       # You are here
├── .gitignore      # Excludes venv, caches, etc.
└── requirements.txt (optional)  # Pin versions for deployment
```

---

## 🧩 Customising the model

Budget data (core, monthly, fixed, optional) lives at the top of `UOF.py` in ordinary Python dictionaries.  Edit those numbers or add new optional costs and the UI will update automatically.

---

## ☁️ Deployment tips

• **Streamlit Community Cloud** – Just push your code; Cloud will read `requirements.txt` and launch.
• **Self-hosting** – Use `streamlit run` behind `nginx` / `docker` / `pm2` as you prefer.

---

## 🤝 Contributing

1. Fork the repo and create your branch:
   ```bash
   git checkout -b feature/my-change
   ```
2. Commit your changes and open a PR.

Issues and feature requests are welcome!

---

## 📄 License

This project is released under the MIT License. See `LICENSE` for details. 