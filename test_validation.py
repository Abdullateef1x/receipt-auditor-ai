from app.services.validation_service import validate_amounts


# Test 1: Matching totals
test_1 = {
    "total_amount": 70.00,
    "tax_included": True,
    "line_items": [
        {"total": 50.00},
        {"total": 10.00},
        {"total": 5.00},
        {"total": 5.00}
    ]
}

# Test 2: Mismatching totals
test_2 = {
    "total_amount": 80.00,
    "tax_included": True,
    "line_items": [
        {"total": 50.00},
        {"total": 10.00},
        {"total": 5.00},
        {"total": 5.00}
    ]
}

# Test 3: No line items
test_3 = {
    "total_amount": 70.00,
    "line_items": []
}

print("TEST 1:", validate_amounts(test_1))
print("TEST 2:", validate_amounts(test_2))
print("TEST 3:", validate_amounts(test_3))    


# Test 4: Difference smaller than one cent
test_4 = {
    "total_amount": 70.005,
    "tax_included": True,
    "line_items": [
        {"total": 70.00}
    ]
}

# Test 5: Missing reported total
test_5 = {
    "line_items": [
        {"total": 70.00}
    ]
}

print("TEST 4:", validate_amounts(test_4))
print("TEST 5:", validate_amounts(test_5))


# Test 6: Tax excluded from line items
test_6 = {
    "total_amount": 108.00,
    "tax": 8.00,
    "tax_included": False,
    "line_items": [
        {"total": 100.00}
    ]
}

# Test 7: Tax already included
test_7 = {
    "total_amount": 100.00,
    "tax": 8.00,
    "tax_included": True,
    "line_items": [
        {"total": 100.00}
    ]
}

# Test 8: Tax inclusion unknown
test_8 = {
    "total_amount": 108.00,
    "tax": 8.00,
    "tax_included": None,
    "line_items": [
        {"total": 100.00}
    ]
}

print("TEST 6:", validate_amounts(test_6))
print("TEST 7:", validate_amounts(test_7))
print("TEST 8:", validate_amounts(test_8))


# Test 9: Tax excluded but tax amount missing
test_9 = {
    "total_amount": 100.00,
    "tax": None,
    "tax_included": False,
    "line_items": [
        {"total": 100.00}
    ]
}

# Test 10: Tax excluded with zero tax
test_10 = {
    "total_amount": 100.00,
    "tax": 0.00,
    "tax_included": False,
    "line_items": [
        {"total": 100.00}
    ]
}

print("TEST 9:", validate_amounts(test_9))
print("TEST 10:", validate_amounts(test_10))


recommendation_messages = {
    "total_amount": "Verify the reported and calculated totals.",
    "tax": "Verify the missing tax amount.",
    "tax_included": "Confirm whether tax is included in line-item totals."
}

test_anomalies = validate_amounts(test_9)

recommendations = [
    recommendation_messages[anomaly["field"]]
    for anomaly in test_anomalies
    if anomaly["field"] in recommendation_messages
]

print("TEST 9 RECOMMENDATIONS:", recommendations)


test_anomalies = validate_amounts(test_8)

recommendations = [
    recommendation_messages[anomaly["field"]]
    for anomaly in test_anomalies
    if anomaly["field"] in recommendation_messages
]

print("TEST 8 RECOMMENDATIONS:", recommendations)
