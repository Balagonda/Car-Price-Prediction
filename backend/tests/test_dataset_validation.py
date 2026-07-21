import pytest
from pydantic import BaseModel, ValidationError

class VehicleDatasetRecord(BaseModel):
    make: str
    model: str
    year: int
    mileage: int

def test_dataset_record_validation():
    # Valid record
    record = VehicleDatasetRecord(make="Toyota", model="Camry", year=2020, mileage=15000)
    assert record.make == "Toyota"
    
    # Invalid record (missing required fields or wrong types)
    with pytest.raises(ValidationError):
        VehicleDatasetRecord(make="Toyota", year="twenty-twenty")
