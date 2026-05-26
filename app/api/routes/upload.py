from app.core.rag import retrieve_relevant_policies
from app.db.database import get_session
from app.models.report import AuditReport
from app.services.ai_service import ai_extraction, analyze_anomalies
from app.services.report_service import generate_audit_report
from app.services.storage_service import upload_report_to_r2
from app.services.upload_service import parse_receipt, save_upload
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pathlib import Path
from sqlmodel import Session, select, desc

router = APIRouter(tags=["Receipts"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    saved = await save_upload(file)
    file_path = saved["file_path"]

    try:
        text = parse_receipt(file_path)
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {e}")

    try:
        extracted_data = ai_extraction(text)
    except Exception as e:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {e}")

    try:
        policy_context = retrieve_relevant_policies(
            f"expense policy for {extracted_data.get('vendor_name', 'unknown vendor')}"
        )
        audit_result = analyze_anomalies(extracted_data, policy_context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly analysis failed: {e}")

    try:
        report_path = generate_audit_report(
            extracted_data=extracted_data,
            audit_result=audit_result,
            original_filename=saved["filename"],
        )
        report_url = upload_report_to_r2(report_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")

    report_id = Path(report_path).stem.split("_")[1]
    record = AuditReport(
        report_id=report_id,
        original_filename=saved["filename"],
        vendor_name=extracted_data.get("vendor_name"),
        invoice_number=extracted_data.get("invoice_number"),
        date=extracted_data.get("date"),
        total_amount=extracted_data.get("total_amount"),
        currency=extracted_data.get("currency"),
        payment_method=extracted_data.get("payment_method"),
        audit_status=audit_result.get("status", "unknown"),
        confidence=audit_result.get("confidence", 0.0),
        recommendation=audit_result.get("recommendation", ""),
        anomalies_count=len(audit_result.get("anomalies", [])),
        report_pdf_url=report_url,
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return {
        "report_id": report_id,
        "status": audit_result.get("status"),
        "anomalies_count": len(audit_result.get("anomalies", [])),
        "recommendation": audit_result.get("recommendation"),
        "confidence": audit_result.get("confidence"),
        "report_url": report_url,       
        "created_at": record.created_at,
    }

@router.get("/reports")
def list_reports(session: Session = Depends(get_session)):
    reports = session.exec(
        select(AuditReport).order_by(desc(AuditReport.created_at))  
    ).all()
    return {
        "total": len(reports),
        "reports": [
            {
                "report_id": r.report_id,
                "filename": r.original_filename,
                "vendor": r.vendor_name,
                "total_amount": r.total_amount,
                "status": r.audit_status,
                "confidence": r.confidence,
                "created_at": r.created_at,
                "pdf_url": r.report_pdf_url,
            }
            for r in reports
        ]
    }
