import numpy as np

# --- Frequency tables (weighted) ---
def weighted_freq(df, col, weight_col='vigt', labels=None):
    freq = df.groupby(col)[weight_col].sum().reset_index()
    freq.columns = [col, 'Weighted N']
    freq['%'] = freq['Weighted N'] / freq['Weighted N'].sum() * 100
    if labels:
        freq[col] = freq[col].map(labels)
    return freq.sort_values('%', ascending=False)


# --- Descriptive stats (weighted) ---
def weighted_stats(df, column, weight):
    d = df[[column, weight]].dropna()
    values = d[column]
    weights = d[weight]
    
    mean = np.average(values, weights=weights)
    variance = np.average((values - mean)**2, weights=weights)
    stddev = np.sqrt(variance)
    
    return {
        'Mean': round(mean, 2),
        'StdDev': round(stddev, 2),
        'Variance': round(variance, 2),
        'Min': int(values.min()),
        'Max': int(values.max())
    }
