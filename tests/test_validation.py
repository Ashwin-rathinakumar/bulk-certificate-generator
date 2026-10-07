def test_validation_empty_recipients(client):
    """Test 2: Input validation for empty recipient list."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_recipients_key(client):
    """Test validation for missing recipients field in payload."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07"
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_name(client):
    """Test input validation for blank recipient name."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": [
            {"name": "   ", "email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_name(client):
    """Test input validation for missing recipient name field."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": [
            {"email": "valid@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_email(client):
    """Test input validation for invalid email address format."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": [
            {"name": "John Doe", "email": "not-an-email"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_email(client):
    """Test input validation for missing recipient email field."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": [
            {"name": "John Doe"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_certificate_title(client):
    """Test input validation for missing certificate title."""
    payload = {
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_organization(client):
    """Test input validation for whitespace-only organization name."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "   ",
        "date": "2026-10-07",
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_date(client):
    """Test input validation for malformed date string."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "07-10-2026",  # Not YYYY-MM-DD
        "recipients": [
            {"name": "John Doe", "email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_field_types(client):
    """Test input validation for invalid field data types."""
    payload = {
        "certificate_title": "Python Workshop",
        "organization": "ABC Technologies",
        "date": "2026-10-07",
        "recipients": "not-a-list"
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
