import QuantLib as ql
import numpy as np

# General parameters
valuationDate = ql.Date(26, 7, 2024)
ql.Settings.instance().evaluationDate = valuationDate
calendar = ql.TARGET()
dayCounter = ql.Actual360()

# Market parameters
spot = 7490.37
strike = 7490.37
r = 0.03  # Risk-free rate
sigma = 0.20  # Volatility
dividendYield = 0.028
CDS = 0.01  # Credit Default Swap spread
T = 5  # Maturity in years
timeSteps = 1000  # Number of time steps for finite difference method
gridPoints = 100  # Number of grid points for price discretization

# Term structure definitions
riskFreeRate = ql.FlatForward(valuationDate, r, dayCounter)
dividendRate = ql.FlatForward(valuationDate, dividendYield, dayCounter)
discountCurve = ql.YieldTermStructureHandle(riskFreeRate)
dividendCurve = ql.YieldTermStructureHandle(dividendRate)
volatility = ql.BlackConstantVol(valuationDate, calendar, sigma, dayCounter)
volatilityHandle = ql.BlackVolTermStructureHandle(volatility)

# Black-Scholes-Merton process
spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
bs_process = ql.BlackScholesMertonProcess(spot_handle, dividendCurve, discountCurve, volatilityHandle)

# Finite difference method engine
fd_engine = ql.FdBlackScholesVanillaEngine(bs_process, timeSteps, gridPoints)

# Product-specific parameters
autoCallBarrier = 1.0 * strike  # 100% of initial level
couponBarrier_Phoenix = 0.7 * strike  # 70% of initial level
protectionBarrier = 0.6 * strike  # 60% of initial level
coupon = 0.05  # 5% per period (10% annualized)
notional = 1_000_000

# Coupon and observation dates
startDate = valuationDate
couponDates = [calendar.advance(startDate, ql.Period(i, ql.Months)) for i in range(6, T * 12 + 1, 6)]

# Define payoff function
def payoff(S, K):
    return max(S - K, 0)

# Pricing function for Phoenix product
def pricePhoenix():
    payoffs = []
    for couponDate in couponDates:
        payoff = ql.PlainVanillaPayoff(ql.Option.Call, couponBarrier_Phoenix)
        exercise = ql.EuropeanExercise(couponDate)
        option = ql.VanillaOption(payoff, exercise)
        option.setPricingEngine(fd_engine)
        payoffs.append(option.NPV())
    return max(payoffs)

# Pricing function for Athena product
def priceAthena():
    payoff = ql.PlainVanillaPayoff(ql.Option.Call, autoCallBarrier)
    exercise = ql.EuropeanExercise(couponDates[-1])
    option = ql.VanillaOption(payoff, exercise)
    option.setPricingEngine(fd_engine)
    return option.NPV()

# Final product valuations
PV_Phoenix = pricePhoenix() * notional / spot
PV_Athena = priceAthena() * notional / spot

print(f"Phoenix product value: {PV_Phoenix}")
print(f"Athena product value: {PV_Athena}")
