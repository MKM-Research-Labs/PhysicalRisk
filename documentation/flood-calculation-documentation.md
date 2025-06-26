# Analytical Flood Probability Calculation Documentation

This document provides a detailed, line-by-line explanation of the Python script used for calculating flood probabilities and statistics.

```python
import numpy as np
```
Imports the NumPy library, which is used for efficient numerical operations.

```python
def calculate_flood_statistics(return_periods, depths):
```
Defines the main function that calculates flood statistics. It takes two parameters:
- `return_periods`: A list of flood return periods (e.g., 10-year flood, 100-year flood)
- `depths`: A list of corresponding flood depths for each return period

```python
    probabilities = 1 / np.array(return_periods)
```
Calculates the annual probability of each flood event by taking the reciprocal of the return periods.

```python
    cumulative_probs = np.cumsum(probabilities)
```
Computes the cumulative probabilities of flood events, representing the probability of experiencing a flood of at least that severity.

```python
    prob_no_flood = 1 - cumulative_probs[-1]
```
Calculates the probability of no flooding occurring in a given year by subtracting the probability of the most extreme event from 1.

```python
    probs = np.diff(np.concatenate(([0], cumulative_probs)))
```
Calculates the individual probabilities for each flood depth:
- `np.concatenate(([0], cumulative_probs))` adds a zero at the beginning of the cumulative probabilities.
- `np.diff()` computes the differences between adjacent elements, giving the probability of each specific flood depth.

```python
    mean_depth = np.sum(probs * depths)
```
Calculates the expected (mean) flood depth by multiplying each depth by its probability and summing the results.

```python
    variance = np.sum(probs * (depths - mean_depth)**2) + prob_no_flood * mean_depth**2
```
Computes the variance of flood depths:
- `probs * (depths - mean_depth)**2` calculates the squared deviation from the mean for each depth, weighted by its probability.
- `prob_no_flood * mean_depth**2` accounts for the contribution of no-flood years to the variance.

```python
    std_dev = np.sqrt(variance)
```
Calculates the standard deviation of flood depths by taking the square root of the variance.

```python
    return mean_depth, std_dev, prob_no_flood, probs
```
Returns the calculated statistics: mean depth, standard deviation, probability of no flooding, and individual probabilities for each depth.

```python
return_periods = [10, 20, 50, 100, 250, 500, 1000]
depths = [0.5, 1.0, 1.5, 2.0, 3.0, 4.5, 6.0]
```
Defines the input data: return periods and corresponding flood depths.

```python
mean, std, prob_no_flood, probs = calculate_flood_statistics(return_periods, depths)
```
Calls the `calculate_flood_statistics` function with the input data and unpacks the returned values.

```python
print(f"Mean Depth (m): {mean:.4f}")
print(f"Standard Deviation (m): {std:.4f}")
print(f"Probability of any flooding: {1-prob_no_flood:.4f}")
```
Prints the calculated mean depth, standard deviation, and probability of any flooding occurring.

```python
print("\nProbability of flooding at each depth:")
for depth, prob in zip(depths, probs):
    print(f"> {depth}m: {prob:.4f}")
```
Prints the probability of flooding at each specific depth.

```python
print("\nCumulative probability of flooding exceeding depth:")
cumulative_probs = np.cumsum(probs[::-1])[::-1]
for depth, cum_prob in zip(depths, cumulative_probs):
    print(f"> {depth}m: {cum_prob:.4f}")
```
Calculates and prints the cumulative probability of flooding exceeding each depth:
- `np.cumsum(probs[::-1])[::-1]` computes the reverse cumulative sum of probabilities.
- The results show the probability of experiencing a flood greater than or equal to each depth.

This script provides a comprehensive analysis of flood probabilities and statistics based on the given return periods and depths, offering valuable insights for flood risk assessment and management.
