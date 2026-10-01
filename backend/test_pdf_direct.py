
from app.services.report_service import ReportService
from jinja2 import Environment, FileSystemLoader
import io
from xhtml2pdf import pisa

env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report.html")

html_out = template.render(
    prediction_id="1234",
    date="October 1, 2026",
    vehicle={
        "brand": "Toyota", "model": "Camry", "year": 2020, "fuel": "Petrol",
        "transmission": "Automatic", "owner": "First", "km": "10,000",
        "city": "Mumbai", "insurance": "Comprehensive", "variant": "Standard"
    },
    estimated_price="1,000,000",
    price_range_min="900,000",
    price_range_max="1,100,000",
    fair_price_status="Fair",
    shap_results=[],
    cv_damage_detected=False,
    cv_damage_severity="None",
    cv_repair_cost="0",
    recommendations=[],
    qr_code=""
)

result_file = io.BytesIO()
pisa_status = pisa.CreatePDF(html_out, dest=result_file)

if pisa_status.err:
    print("PDF generation error")
else:
    print("Success! Size:", len(result_file.getvalue()))

