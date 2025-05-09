# Structured Products in France 🇫🇷📈

This repository contains the final thesis and Python pricing models developed as part of my thesis in **Market Finance and Risk Management** at **Université Paris 1 Panthéon-Sorbonne**.

## 🎓 Thesis Overview

The report provides an in-depth analysis of the structured products market in France, with a particular focus on **autocallable instruments** such as Athena and Phoenix structures. Key topics include:

- Classification and characteristics of structured products (capital protection, yield enhancement, participation, leverage)
- Regulatory landscape: MiFID II, PRIIPs, and AMF best practices
- Market evolution, investor behavior, and the role of insurers and financial advisors
- Quantitative pricing methods: Monte Carlo simulation, Black-Scholes PDEs, and the Heston model
- Hedging strategies and the impact of regulations on pricing and product design

📄 [Read the full thesis PDF](report/Structured_Products_in_France_Report.pdf)


## 🧠 Code Purpose

This repository also includes two Python scripts that reproduce and extend the numerical analysis developed in the thesis. These scripts implement pricing engines for structured products under different assumptions:

### `pricing_heston.py`
- Simulates asset price paths under the **Heston stochastic volatility model**
- Calibrates the model to market volatility data
- Prices **Athena and Phoenix autocallable notes** using Monte Carlo simulations
- Computes the **investment percentage** needed to replicate these products

### `pricing_monte_carlo.py`
- Implements a pricing framework under the **Black-Scholes model**
- Uses finite difference methods (FDM) to price European options
- Approximates the value of autocallable products with fixed barriers and coupon structures
- Serves as a simpler benchmark for comparison with the Heston model

These models illustrate how different assumptions affect the valuation and risk profile of structured products in a realistic French market context.

## 📦 Installation

To run the code, install the required Python dependencies:

```bash
pip install -r requirements.txt
```

### `requirements.txt`

```txt
QuantLib-Python
numpy
scipy
```

## 📁 Repository Structure

```
structured-products-france/
├── README.md
├── report/
│   └── Structured_Products_in_France.pdf
├── code/
│   ├── pricing_heston.py
│   └── pricing_monte_carlo.py
├── requirements.txt
└── LICENSE
```

## ⚖️ License

This project is open-source and available under the [MIT License](LICENSE).
