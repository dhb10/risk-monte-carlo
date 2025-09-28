import numpy as np

def sample_distribution(dist, params, size):
    if dist == "normal":
        return np.random.normal(params["mean"], params["stddev"], size)
    elif dist == "triangular":
        return np.random.triangular(params["min"], params["mode"], params["max"], size)
    elif dist == "uniform":
        return np.random.uniform(params["min"], params["max"], size)
    elif dist == "lognormal":
        return np.random.lognormal(params["mean"], params["stddev"], size)
    else:
        raise ValueError(f"Unsupported distribution: {dist}")

def run_simulation(variables, formula, num_trials):
    samples = {}
    for var in variables:
        samples[var["name"]] = sample_distribution(
            var["distribution"], var["parameters"], num_trials
        )

    # Evaluate formula: e.g., "revenue - cost"
    result = eval(formula, {}, samples)
    return result
