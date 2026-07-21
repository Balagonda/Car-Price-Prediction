import base64
import io
import logging
import uuid
from datetime import datetime

import qrcode
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession
from weasyprint import HTML

from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._prediction_service = PredictionService(db)
        
        # Setup Jinja2 environment pointing to templates directory
        self._env = Environment(loader=FileSystemLoader("app/templates"))

    async def generate_prediction_report(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> bytes:
        """
        Generate a PDF report for a given prediction.
        """
        # Fetch the full prediction detail using PredictionService
        prediction = await self._prediction_service.get_prediction_detail(prediction_id, user_id)
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found."
            )

        # Generate QR code for verification (could point to a public verify URL in a real app)
        qr_data = f"AutoWorth AI Report Verify: {prediction.id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        qr_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # We need the vehicle details. prediction object is a PredictionResponse which doesn't have 
        # all vehicle details directly at the top level, but it has `similar_vehicles`. 
        # Wait, the `PredictionResponse` doesn't include the input vehicle specs.
        # We need to fetch the Vehicle from DB to populate the report properly.
        
        from app.repositories.prediction_repository import PredictionRepository
        pred_record = await PredictionRepository(self._db).get_with_full_details(prediction_id)
        if not pred_record or not pred_record.vehicle:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction or Vehicle not found."
            )
        
        v = pred_record.vehicle
        
        from app.repositories.vehicle_repository import VehicleRepository
        v_repo = VehicleRepository(self._db)
        brand_name = await v_repo.get_brand_name(v.brand_id)
        model_name = await v_repo.get_model_name(v.car_model_id)
        city_name = await v_repo.get_city_name(v.city_id) if v.city_id else "Unknown"

        vehicle_dict = {
            "brand": brand_name,
            "model": model_name,
            "year": v.manufacturing_year,
            "fuel": v.fuel_type.value.capitalize(),
            "transmission": v.transmission.value.capitalize(),
            "owner": v.owner_type.value.capitalize().replace("_", " "),
            "km": f"{v.kilometers_driven:,}",
            "city": city_name,
            "insurance": v.insurance_status.value.capitalize().replace("_", " "),
            "variant": "Standard" # We don't have variant name easily without extra lookup, keep it simple
        }
        
        # Format prices
        def format_inr(value: float) -> str:
            return f"₹{value:,.0f}"

        template = self._env.get_template("report.html")
        html_out = template.render(
            prediction_id=str(prediction.id),
            date=prediction.created_at.strftime("%B %d, %Y"),
            vehicle=vehicle_dict,
            estimated_price=format_inr(prediction.estimated_price),
            price_range_min=format_inr(prediction.price_range_min),
            price_range_max=format_inr(prediction.price_range_max),
            fair_price_status=prediction.fair_price_status,
            shap_results=[s.model_dump() for s in prediction.shap_results],
            cv_damage_detected=prediction.cv_damage_detected,
            cv_damage_severity=prediction.cv_damage_severity,
            cv_repair_cost=format_inr(prediction.cv_repair_cost_estimate) if prediction.cv_repair_cost_estimate else "N/A",
            recommendations=[r.model_dump() for r in prediction.recommendations],
            qr_code=qr_base64
        )

        # Convert HTML to PDF using WeasyPrint
        pdf_bytes = HTML(string=html_out).write_pdf()
        
        return pdf_bytes
