"""
Tests for service history and document management endpoints
"""
import io
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.service_history import ServiceHistory, ServiceDocument


def create_test_pdf():
    """Create a minimal valid PDF file for testing"""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
190
%%EOF"""
    return io.BytesIO(pdf_content)


class TestCreateServiceHistory:
    """Test service history creation"""

    def test_create_service_history_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful service history creation"""
        service_date = datetime.utcnow().isoformat()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers,
            json={
                "service_date": service_date,
                "provider": "Rolex Service Center",
                "service_type": "Full Service",
                "description": "Complete overhaul and cleaning",
                "cost": 850.00,
                "cost_currency": "USD",
                "next_service_due": (datetime.utcnow() + timedelta(days=1825)).isoformat()
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["watch_id"] == str(test_watch.id)
        assert data["provider"] == "Rolex Service Center"
        assert data["service_type"] == "Full Service"
        assert data["cost"] == "850.00"  # Cost is returned as string
        assert data["cost_currency"] == "USD"
        assert "id" in data
        assert "documents" in data

    def test_create_service_history_with_optional_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test creating service history with only required fields"""
        service_date = datetime.utcnow().isoformat()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers,
            json={
                "service_date": service_date,
                "provider": "Local Watchmaker"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "Local Watchmaker"
        assert data["service_type"] is None
        assert data["description"] is None
        assert data["cost"] is None

    def test_create_service_history_validates_required_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test validation of required fields"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers,
            json={"service_date": datetime.utcnow().isoformat()}  # Missing provider
        )

        assert response.status_code == 422

    def test_create_service_history_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test creating service history without authentication"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history",
            json={
                "service_date": datetime.utcnow().isoformat(),
                "provider": "Test"
            }
        )

        assert response.status_code == 401

    def test_create_service_history_wrong_owner(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch
    ):
        """Test creating service history for another user's watch"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers2,
            json={
                "service_date": datetime.utcnow().isoformat(),
                "provider": "Test"
            }
        )

        assert response.status_code == 404


class TestListServiceHistory:
    """Test service history listing"""

    def test_list_service_history_sorted_by_date(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that service history is sorted by date (most recent first)"""
        # Create three service records with different dates
        dates = [
            datetime.utcnow() - timedelta(days=730),  # 2 years ago
            datetime.utcnow() - timedelta(days=365),  # 1 year ago
            datetime.utcnow() - timedelta(days=30),   # 1 month ago
        ]

        for i, date in enumerate(dates):
            service = ServiceHistory(
                watch_id=test_watch.id,
                service_date=date,
                provider=f"Provider {i}"
            )
            test_db.add(service)
        test_db.commit()

        # List service history
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

        # Verify ordering (most recent first)
        assert data[0]["provider"] == "Provider 2"  # Most recent
        assert data[1]["provider"] == "Provider 1"
        assert data[2]["provider"] == "Provider 0"  # Oldest

    def test_list_service_history_includes_documents(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that service history includes related documents"""
        # Create service with document
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Add document
        document = ServiceDocument(
            service_history_id=service.id,
            file_path=f"{test_watch.id}/{service.id}/receipt.pdf",
            file_name="receipt.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        test_db.add(document)
        test_db.commit()

        # List service history
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert len(data[0]["documents"]) == 1
        assert data[0]["documents"][0]["file_name"] == "receipt.pdf"

    def test_list_service_history_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test listing service history when none exist"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_service_history_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test listing without authentication"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history"
        )

        assert response.status_code == 401


class TestGetServiceHistory:
    """Test getting individual service history record"""

    def test_get_service_history_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test getting a specific service record"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider",
            cost=500.00
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(service.id)
        assert data["provider"] == "Test Provider"
        assert data["cost"] == "500.00"  # Cost is returned as string

    def test_get_service_history_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test getting non-existent service record"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateServiceHistory:
    """Test service history updates"""

    def test_update_service_history_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful service history update"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Original Provider",
            cost=500.00
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers,
            json={
                "provider": "Updated Provider",
                "cost": 750.00
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "Updated Provider"
        assert data["cost"] == "750.00"  # Cost is returned as string

    def test_update_service_history_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test partial update (only some fields)"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider",
            cost=500.00,
            description="Original description"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers,
            json={"description": "Updated description"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["provider"] == "Test Provider"  # Unchanged
        assert data["cost"] == "500.00"  # Unchanged, cost is returned as string

    def test_update_service_history_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test updating another user's service record"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers2,
            json={"provider": "Hacked"}
        )

        assert response.status_code == 404


class TestDeleteServiceHistory:
    """Test service history deletion"""

    def test_delete_service_history_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful service history deletion"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        service_id = service.id

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(ServiceHistory).filter(
            ServiceHistory.id == service_id
        ).first()
        assert deleted is None

    def test_delete_service_history_cascades_to_documents(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test that deleting service history also deletes documents"""
        # Create service with document
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        document = ServiceDocument(
            service_history_id=service.id,
            file_path=f"{test_watch.id}/{service.id}/receipt.pdf",
            file_name="receipt.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        test_db.add(document)
        test_db.commit()
        document_id = document.id

        # Delete service
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify document is also deleted
        deleted_doc = test_db.query(ServiceDocument).filter(
            ServiceDocument.id == document_id
        ).first()
        assert deleted_doc is None

    def test_delete_service_history_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test deleting another user's service record"""
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404


class TestServiceDocuments:
    """Test service document upload and management"""

    def test_upload_service_document_pdf(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test uploading a PDF document"""
        # Create service record
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Upload PDF
        pdf_file = create_test_pdf()
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents",
            headers=auth_headers,
            files={"file": ("receipt.pdf", pdf_file, "application/pdf")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["service_history_id"] == str(service.id)
        assert data["file_name"] == "receipt.pdf"
        assert data["mime_type"] == "application/pdf"
        assert "url" in data

    def test_upload_service_document_image(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test uploading an image as a document"""
        from PIL import Image as PILImage

        # Create service record
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Create test image
        img = PILImage.new("RGB", (100, 100), color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        # Upload image
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents",
            headers=auth_headers,
            files={"file": ("receipt.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "receipt.jpg"
        assert data["mime_type"] == "image/jpeg"

    def test_upload_service_document_validates_type(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test that only valid document types are accepted"""
        # Create service record
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Try to upload invalid file type
        text_file = io.BytesIO(b"Not a valid document")
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents",
            headers=auth_headers,
            files={"file": ("invalid.txt", text_file, "text/plain")}
        )

        assert response.status_code == 400

    def test_upload_service_document_validates_size(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test document size validation (10MB limit)"""
        # Create service record
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Create large file (11MB)
        large_file = io.BytesIO(b"x" * (11 * 1024 * 1024))
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents",
            headers=auth_headers,
            files={"file": ("large.pdf", large_file, "application/pdf")}
        )

        assert response.status_code == 400
        assert "10MB" in response.json()["detail"]

    def test_list_service_documents_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test listing documents for a service record"""
        # Create service with documents
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        # Add two documents
        for i in range(2):
            document = ServiceDocument(
                service_history_id=service.id,
                file_path=f"{test_watch.id}/{service.id}/doc{i}.pdf",
                file_name=f"doc{i}.pdf",
                file_size=1024,
                mime_type="application/pdf"
            )
            test_db.add(document)
        test_db.commit()

        # List documents
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_delete_service_document_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        mock_upload_dir
    ):
        """Test deleting a service document"""
        # Create service with document
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        document = ServiceDocument(
            service_history_id=service.id,
            file_path=f"{test_watch.id}/{service.id}/receipt.pdf",
            file_name="receipt.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        test_db.add(document)
        test_db.commit()
        document_id = document.id

        # Delete document
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents/{document_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(ServiceDocument).filter(
            ServiceDocument.id == document_id
        ).first()
        assert deleted is None

    def test_delete_service_document_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test deleting non-existent document"""
        # Create service
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_service_document_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test deleting another user's document"""
        # Create service with document
        service = ServiceHistory(
            watch_id=test_watch.id,
            service_date=datetime.utcnow(),
            provider="Test Provider"
        )
        test_db.add(service)
        test_db.commit()
        test_db.refresh(service)

        document = ServiceDocument(
            service_history_id=service.id,
            file_path=f"{test_watch.id}/{service.id}/receipt.pdf",
            file_name="receipt.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        test_db.add(document)
        test_db.commit()

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/service-history/{service.id}/documents/{document.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404
