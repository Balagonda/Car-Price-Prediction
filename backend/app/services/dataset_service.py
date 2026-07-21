"""
AutoWorth AI — Dataset Service

Handles dataset upload, validation, deduplication, and persistence.
"""

import os
import uuid
import pandas as pd
from pathlib import Path
from fastapi import UploadFile

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.dataset_repository import DatasetRepository
from app.models.dataset import Dataset
from app.models.user import User

DATA_DIR = Path("data/datasets")
DATA_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = {
    "brand", "model", "manufacturing_year", "fuel_type",
    "transmission", "owner_type", "seller_type", "kilometers_driven",
    "selling_price",
}

class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DatasetRepository(db)

    async def process_upload(
        self,
        file: UploadFile,
        mode: str,
        version: str,
        user: User
    ) -> dict:
        """
        Process the uploaded CSV file.
        mode can be "replace" or "merge".
        """
        if not file.filename.endswith(".csv"):
            raise ValueError("Only CSV files are allowed.")
        
        # Read uploaded file into pandas
        try:
            df = pd.read_csv(file.file, low_memory=False)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")
            
        # Normalize column names for validation
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        # Validate columns
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(f"Dataset is missing required columns: {missing_cols}")
            
        initial_len = len(df)
        
        # Optional: remove entirely invalid rows before deduplication
        df = df.dropna(subset=list(REQUIRED_COLUMNS))
        invalid_rows = initial_len - len(df)
        
        # Handle merge/replace
        if mode == "merge":
            latest_ds = await self.repo.get_latest_dataset()
            if latest_ds and latest_ds.file_url:
                try:
                    existing_df = pd.read_csv(latest_ds.file_url, low_memory=False)
                    df = pd.concat([existing_df, df], ignore_index=True)
                except Exception:
                    pass # Proceed with just the new df if reading old fails
        elif mode == "replace":
            await self.repo.deactivate_all_datasets()
            
        # Deduplicate
        before_dedup = len(df)
        df = df.drop_duplicates()
        duplicates_removed = before_dedup - len(df)
        
        # Save to disk
        file_id = uuid.uuid4()
        file_path = DATA_DIR / f"dataset_{version}_{file_id}.csv"
        df.to_csv(file_path, index=False)
        
        dataset = await self.repo.create(
            name=f"Dataset {version} ({mode})",
            version=version,
            description=f"Uploaded via Admin Panel. Mode: {mode}",
            file_url=str(file_path.absolute()),
            original_filename=file.filename,
            row_count=len(df),
            column_count=len(df.columns),
            file_size_bytes=os.path.getsize(file_path),
            duplicate_rows_removed=duplicates_removed,
            invalid_rows_removed=invalid_rows,
            uploaded_by_id=user.id,
            is_active=True
        )
        
        return {
            "dataset_id": dataset.id,
            "name": dataset.name,
            "version": dataset.version,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "duplicate_rows_removed": duplicates_removed,
            "invalid_rows_removed": invalid_rows,
            "message": "Dataset processed and saved successfully."
        }
