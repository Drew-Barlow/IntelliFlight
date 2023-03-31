import pytest
import json
from pathlib import Path
from intelliflight.models.components.dataset import Dataset
from typing import Final


## DATA ##


TEST_PATH: Final = Path(__file__).parent.parent
FIFTY_FLIGHTS_PATH: Final = TEST_PATH / 'data' / 'fifty_flights.json'


## HELPERS ##


def setup() -> Dataset:
    """Instantiate and return a Dataset object."""
    data = json.load(FIFTY_FLIGHTS_PATH.open())
    dataset = Dataset()
    dataset.set_data(data)
    return dataset


## TESTS ##


@pytest.mark.unit
@pytest.mark.dataset
def test_set_data():
    """Load data and verify that data and data_len fields are set correctly."""
    # Don't use setup() because we need access to the input dataset
    data = json.load(FIFTY_FLIGHTS_PATH.open())
    dataset = Dataset()
    dataset.set_data(data[:])
    assert dataset.get_data() == data
    assert dataset.get_len() == len(data)


@pytest.mark.unit
@pytest.mark.dataset
def test_set_test_bounds():
    """Set and read valid data test bounds."""
    dataset = setup()
    bounds = (10, 20)
    dataset.set_test_bounds(*bounds)
    assert dataset.get_test_bounds() == bounds


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('bounds', [(-1, 10), (60, 70)])
def test_set_test_bounds_start_out_of_range(bounds: tuple[int, int]):
    """Attempt to set test bounds with the start index out-of-bounds."""
    with pytest.raises(IndexError):
        dataset = setup()
        dataset.set_test_bounds(*bounds)


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('bounds', [(10, 70)])
def test_set_test_bounds_end_out_of_range(bounds: tuple[int, int]):
    """Attempt to set test bounds with the end index out-of-bounds."""
    with pytest.raises(IndexError):
        dataset = setup()
        dataset.set_test_bounds(*bounds)


@pytest.mark.unit
@pytest.mark.dataset
def test_set_test_bounds_start_above_end():
    """Attempt to set test bounds with the start > end."""
    with pytest.raises(ValueError):
        dataset = setup()
        dataset.set_test_bounds(10, 5)


@pytest.mark.unit
@pytest.mark.dataset
def test_clear_test_bounds():
    """Test whether test bounds are properly cleared."""
    dataset = setup()
    dataset.set_test_bounds(1, 2)
    dataset.clear_test_partition()
    assert dataset.get_test_bounds() == (None, None)


@pytest.mark.unit
@pytest.mark.dataset
def test_set_validation_bounds():
    """Set and read valid data validation bounds."""
    dataset = setup()
    bounds = (10, 20)
    dataset.set_validation_bounds(*bounds)
    assert dataset.get_validation_bounds() == bounds


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('bounds', [(-1, 10), (60, 70)])
def test_set_validation_bounds_start_out_of_range(bounds: tuple[int, int]):
    """Attempt to set validation bounds with the start index out-of-bounds."""
    with pytest.raises(IndexError):
        dataset = setup()
        dataset.set_validation_bounds(*bounds)


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('bounds', [(10, 70)])
def test_set_validation_bounds_end_out_of_range(bounds: tuple[int, int]):
    """Attempt to set validation bounds with the end index out-of-bounds."""
    with pytest.raises(IndexError):
        dataset = setup()
        dataset.set_validation_bounds(*bounds)


@pytest.mark.unit
@pytest.mark.dataset
def test_set_validation_bounds_start_above_end():
    """Attempt to set validation bounds with the start > end."""
    with pytest.raises(ValueError):
        dataset = setup()
        dataset.set_validation_bounds(10, 5)


@pytest.mark.unit
@pytest.mark.dataset
def test_clear_validation_bounds():
    """Test whether validation bounds are properly cleared."""
    dataset = setup()
    dataset.set_validation_bounds(1, 2)
    dataset.clear_validation_partition()
    assert dataset.get_validation_bounds() == (None, None)


@pytest.mark.unit
@pytest.mark.dataset
def test_get_training_len_with_test_part():
    """Test getting data length minus test segment."""
    dataset = setup()
    dataset.set_test_bounds(0, 5)
    assert dataset.get_training_len() == (dataset.get_len() - 5)


@pytest.mark.unit
@pytest.mark.dataset
def test_get_training_len_with_validation_part():
    """Test getting data length minus validation segment."""
    dataset = setup()
    dataset.set_validation_bounds(0, 5)
    assert dataset.get_training_len() == (dataset.get_len() - 5)


@pytest.mark.unit
@pytest.mark.dataset
def test_get_training_len_with_test_and_validation_part():
    """Test getting data length minus test and validation segments."""
    dataset = setup()
    dataset.set_test_bounds(0, 5)
    dataset.set_validation_bounds(5, 10)
    assert dataset.get_training_len() == (dataset.get_len() - 10)


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('test_bounds, validation_bounds', [
    ((0, 5), (4, 9)),
    ((4, 9), (0, 5))
])
def test_get_training_len_with_overlapping_partitions(
        test_bounds: tuple[int, int], validation_bounds: tuple[int, int]):
    """Test getting training data length when test and validation segments
    overlap."""
    dataset = setup()
    dataset.set_test_bounds(*test_bounds)
    dataset.set_validation_bounds(*validation_bounds)
    assert dataset.get_training_len() == (dataset.get_len() - 9)


@pytest.mark.unit
@pytest.mark.dataset
@pytest.mark.parametrize('dataset, expected', [
    (setup(), True),
    (Dataset(), False)
])
def test_data_is_loaded(dataset: Dataset, expected: bool):
    """Test detection of data loading state."""
    assert dataset.data_loaded() == expected


@pytest.mark.unit
@pytest.mark.dataset
def test_get_data_no_data():
    """Attempt to get an unloaded dataset."""
    with pytest.raises(ValueError):
        Dataset().get_data()


@pytest.mark.unit
@pytest.mark.dataset
def test_get_len_no_data():
    """Attempt to get length of an unloaded dataset."""
    with pytest.raises(ValueError):
        Dataset().get_len()


@pytest.mark.unit
@pytest.mark.dataset
def test_get_training_len_no_data():
    """Attempt to get training length of an unloaded dataset."""
    with pytest.raises(ValueError):
        Dataset().get_training_len()


@pytest.mark.unit
@pytest.mark.dataset
def test_set_test_bounds_no_data():
    """Attempt to set test bounds of an unloaded dataset."""
    with pytest.raises(ValueError):
        Dataset().set_test_bounds(0, 1)


@pytest.mark.unit
@pytest.mark.dataset
def test_set_validation_bounds_no_data():
    """Attempt to set validation bounds of an unloaded dataset."""
    with pytest.raises(ValueError):
        Dataset().set_validation_bounds(0, 1)
