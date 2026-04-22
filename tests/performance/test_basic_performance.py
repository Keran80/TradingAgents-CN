"""Performance tests for critical operations."""
import pytest
import time
import pandas as pd
import numpy as np

def test_dataframe_creation_performance():
    """Test DataFrame creation performance."""
    start_time = time.time()
    df = pd.DataFrame({'value': np.random.randn(1000)})
    creation_time = time.time() - start_time
    assert creation_time < 0.1

def test_vectorized_operations():
    """Test performance of vectorized operations."""
    array = np.random.randn(10000)
    start_time = time.time()
    result = array * 2 + 1
    vectorized_time = time.time() - start_time
    assert vectorized_time < 0.01
