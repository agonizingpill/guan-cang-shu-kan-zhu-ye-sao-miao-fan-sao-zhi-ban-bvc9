from hashlib import sha256
from math import ceil
import json

import numpy as np
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance

def features(row):
    return [int(row['feed']=='cradle'), row['gutter']]

def exposure(row):
    return row['last']-row['first']+1

def calculate(data):
    rows = data['history']
    train, test = rows[:-6], rows[-6:]
    weights = np.asarray([exposure(row) for row in train])
    counts = np.asarray([len(row['faults']) for row in train])
    model = PoissonRegressor(alpha=.015,max_iter=200).fit(
        [features(row) for row in train], counts/weights, sample_weight=weights)
    test_exposures = np.asarray([exposure(row) for row in test])
    test_counts = [len(row['faults']) for row in test]
    forecast = float(model.predict([features(data['check'])])[0])*exposure(data['check'])
    return {'algorithm':'PoissonRegressor','expected_count':round(forecast,4),
            'planned_pages':ceil(forecast),'exposure_pages':exposure(data['check']),
            'training_segments':len(train),'holdout_segments':len(test),
            'holdout_mean_poisson_deviance':round(mean_poisson_deviance(
                test_counts,model.predict([features(row) for row in test])*test_exposures),5),
            'constant_mean_poisson_deviance':round(mean_poisson_deviance(
                test_counts,counts.sum()/weights.sum()*test_exposures),5),
            'input_hash':sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()}
