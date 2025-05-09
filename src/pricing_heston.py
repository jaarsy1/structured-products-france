import QuantLib as ql
import numpy as np
import scipy.optimize as opt

# Path generation under the Heston model
def HestonPathGenerator(dates, dayCounter, process, nPaths):
    t = np.array([dayCounter.yearFraction(dates[0], d) for d in dates])
    nGridSteps = (t.shape[0] - 1) * 2
    sequenceGenerator = ql.UniformRandomSequenceGenerator(nGridSteps, ql.UniformRandomGenerator())
    gaussianSequenceGenerator = ql.GaussianRandomSequenceGenerator(sequenceGenerator)
    pathGenerator = ql.GaussianMultiPathGenerator(process, t, gaussianSequenceGenerator, False)
    paths = np.zeros(shape=(nPaths, t.shape[0]))
    
    for i in range(nPaths):
        multiPath = pathGenerator.next().value()
        paths[i, :] = np.array(list(multiPath[0]))
        
    return paths

# Heston model calibration
def HestonModelCalibrator(valuationDate, calendar, spot, curveHandle, dividendHandle, 
    v0, kappa, theta, sigma, rho, expiration_dates, strikes, data, optimizer, bounds):
    
    helpers = []
    process = ql.HestonProcess(curveHandle, dividendHandle, 
        ql.QuoteHandle(ql.SimpleQuote(spot)), v0, kappa, theta, sigma, rho)
    model = ql.HestonModel(process)
    engine = ql.AnalyticHestonEngine(model)
    
    def CostFunction(x):
        parameters = ql.Array(list(x))        
        model.setParams(parameters)
        error = [helper.calibrationError() for helper in helpers]
        return np.sqrt(np.sum(np.abs(error)))

    for i in range(len(expiration_dates)):
        for j in range(len(strikes)):
            expiration = expiration_dates[i]
            days = expiration - valuationDate
            period = ql.Period(days, ql.Days)
            vol = data[i][j]
            strike = strikes[j]
            helper = ql.HestonModelHelper(period, calendar, spot, strike,
                ql.QuoteHandle(ql.SimpleQuote(vol)), curveHandle, dividendHandle)
            helper.setPricingEngine(engine)
            helpers.append(helper)
    
    optimizer(CostFunction, bounds)
    return process, model

# Autocallable product valuation
def AutoCallableNote(valuationDate, couponDates, strike, pastFixings, 
    autoCallBarrier, couponBarrier, protectionBarrier, hasMemory, finalRedemptionFormula, 
    coupon, notional, dayCounter, process, generator, nPaths, curve):    
    
    if valuationDate >= couponDates[-1]:
        return 0.0
    
    if valuationDate >= couponDates[0]:
        if max(pastFixings.values()) >= (autoCallBarrier * strike):
            return 0.0

    dates = np.hstack((np.array([valuationDate]), couponDates[couponDates > valuationDate]))
    paths = generator(dates, dayCounter, process, nPaths)[:, 1:]
    
    pastDates = couponDates[couponDates <= valuationDate]
    if pastDates.shape[0] > 0:
        pastFixingsArray = np.array([pastFixings[pastDate] for pastDate in pastDates])        
        pastFixingsArray = np.tile(pastFixingsArray, (paths.shape[0], 1))
        paths = np.hstack((pastFixingsArray, paths))
    
    global_pv = []
    expirationDate = couponDates[-1]
    hasMemory = int(hasMemory)
    
    for path in paths:
        payoffPV = 0.0
        unpaidCoupons = 0
        hasAutoCalled = False
        
        for date, index in zip(couponDates, (path / strike)):
            if hasAutoCalled:
                break
            payoff = 0.0
                
            if date == expirationDate:
                if index >= couponBarrier:
                    payoff = notional * (1 + (coupon * (1 + unpaidCoupons * hasMemory)))
                elif index >= protectionBarrier:
                    payoff = notional
                else:
                    index = index * strike
                    payoff = notional * finalRedemptionFormula(index)
            else:
                if index >= autoCallBarrier:
                    payoff = notional * (1 + (coupon * (1 + unpaidCoupons * hasMemory)))
                    hasAutoCalled = True
                elif index >= couponBarrier:
                    payoff = notional * (coupon * (1 + unpaidCoupons * hasMemory))
                    unpaidCoupons = 0
                else:
                    unpaidCoupons += 1

            if date > valuationDate:
                df = curve.discount(date)
                payoffPV += payoff * df
            
        global_pv.append(payoffPV)
        
    return np.mean(np.array(global_pv))

# General parameters
valuationDate = ql.Date(20, 7, 2024)
ql.Settings.instance().evaluationDate = valuationDate
calendar = ql.TARGET()
dayCounter = ql.Actual360()

# Interest rate curves
curveHandle = ql.YieldTermStructureHandle(ql.FlatForward(valuationDate, 0.02, dayCounter))
dividendHandle = ql.YieldTermStructureHandle(ql.FlatForward(valuationDate, 0.028, dayCounter))

notional = 1000000.0
spot = 79.98
strike = 79.98
autoCallBarrier = 1.0
couponBarrier = 0.7
protectionBarrier = 0.6
coupon = 0.05
hasMemory = True

# Coupon dates
startDate = valuationDate
firstCouponDate = calendar.advance(startDate, ql.Period(6, ql.Months))
lastCouponDate = calendar.advance(startDate, ql.Period(5, ql.Years))
couponDates = np.array(list(ql.Schedule(firstCouponDate, lastCouponDate, ql.Period(ql.Semiannual), 
    calendar, ql.ModifiedFollowing, ql.ModifiedFollowing, ql.DateGeneration.Forward, False)))

pastFixings = {}

expiration_dates = [ql.Date(20,1,2025), ql.Date(20,7,2025), 
    ql.Date(20,1,2026), ql.Date(20,7,2026), ql.Date(20,1,2027)]

strikes = [79.98 * x for x in [0.7, 0.8, 0.9, 1.0, 1.1]]
data = [[0.3565 for _ in strikes] for _ in expiration_dates]

theta = 0.01
kappa = 0.5
sigma = 0.2
rho = -0.5
v0 = 0.01

bounds = [(0.01, 1.0), (0.01, 10.0), (0.01, 1.0), (-1.0, 1.0), (0.01, 1.0)]

calibrationResult = HestonModelCalibrator(valuationDate, calendar, spot, curveHandle, dividendHandle, 
        v0, kappa, theta, sigma, rho, expiration_dates, strikes, data, opt.differential_evolution, bounds)

print('Calibrated Heston parameters:', calibrationResult[1].params())

nPaths = 10000

# Athena product
autoCallBarrier_Athena = 1.0
couponBarrier_Athena = 1.0

PV_Athena = AutoCallableNote(valuationDate, couponDates, strike, pastFixings, 
    autoCallBarrier_Athena, couponBarrier_Athena, protectionBarrier, hasMemory, lambda x: x / strike, 
    coupon, notional, dayCounter, calibrationResult[0], HestonPathGenerator, nPaths, curveHandle)

# Phoenix product
autoCallBarrier_Phoenix = 1.0
couponBarrier_Phoenix = 0.7

PV_Phoenix = AutoCallableNote(valuationDate, couponDates, strike, pastFixings, 
    autoCallBarrier_Phoenix, couponBarrier_Phoenix, protectionBarrier, hasMemory, lambda x: x / strike, 
    coupon, notional, dayCounter, calibrationResult[0], HestonPathGenerator, nPaths, curveHandle)

# Purchase percentages
r = 0.045
T = 5

present_value_athena = PV_Athena / ((1 + r) ** T)
present_value_phoenix = PV_Phoenix / ((1 + r) ** T)

purchase_percentage_athena = (present_value_athena / notional) * 100
purchase_percentage_phoenix = (present_value_phoenix / notional) * 100

print(f"Athena purchase percentage: {purchase_percentage_athena:.2f}%")
print(f"Phoenix purchase percentage: {purchase_percentage_phoenix:.2f}%")
