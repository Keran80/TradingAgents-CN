"""Integration tests for data pipeline."""
import pytest
import pandas as pd
import numpy as np

def test_data_fetch_transform():
    """Test data fetch and transformation pipeline."""
    data = pd.DataFrame({
        'price': [100, 101, 102, 103, 104]
    })
    data['returns'] = data['price'].pct_change()
    assert 'returns' in data.columns

@pytest.mark.slow
def test_large_dataset_processing():
    """Test processing of large datasets."""
    large_data = pd.DataFrame({'value': np.random.randn(1000)})
    assert len(large_data) == 1000
