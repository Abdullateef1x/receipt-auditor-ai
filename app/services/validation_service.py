def validate_amounts(extracted_data: dict) -> list[dict]:
    anomalies = []

    line_items = extracted_data.get("line_items", [])
    reported_total = extracted_data.get("total_amount")
    tax = extracted_data.get("tax")
    tax_included = extracted_data.get("tax_included")

    if line_items and reported_total is not None:

        calculated_total = sum(
            item.get("total", 0) for item in line_items
        )

        if tax_included is False:
            if tax is None:
                anomalies.append({
                    "field": "tax",
                    "issue": (
                        "Tax is excluded from line items, "
                        "but the tax amount is missing. "
                        "Manual verification required."
                    ),
                    "severity": "medium"
                })
                return anomalies

            calculated_total += tax

        elif tax_included is None:
            anomalies.append({
                "field": "tax_included",
                "issue": (
                    "Unable to determine whether tax is "
                    "already included in line-item totals. "
                    "Manual verification required."
                ),
                "severity": "medium"
            })
            return anomalies

        if abs(calculated_total - reported_total) > 0.01:
            anomalies.append({
                "field": "total_amount",
                "issue": (
                    f"Reported total ({reported_total}) "
                    f"does not match calculated total "
                    f"({calculated_total})."
                ),
                "severity": "medium"
            })

    return anomalies