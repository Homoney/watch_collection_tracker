"""
Tests for watch image upload and management endpoints
"""
import io
import pytest
from PIL import Image as PILImage
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.watch_image import WatchImage


def create_test_image(width=100, height=100, format="JPEG"):
    """
    Create a test image file in memory.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (JPEG, PNG, etc.)

    Returns:
        BytesIO object containing the image data
    """
    img = PILImage.new("RGB", (width, height), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


class TestUploadImage:
    """Test image upload endpoint"""

    def test_upload_image_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test successful image upload"""
        img_bytes = create_test_image(800, 600)

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["watch_id"] == str(test_watch.id)
        assert data["file_name"] == "test.jpg"
        assert data["mime_type"] == "image/jpeg"
        assert data["width"] == 800
        assert data["height"] == 600
        assert data["is_primary"] is True  # First image should be primary
        assert data["sort_order"] == 0
        assert data["source"] == "user_upload"
        assert "url" in data

    def test_upload_image_sets_first_as_primary(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test that first uploaded image is set as primary"""
        img_bytes = create_test_image()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("first.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_primary"] is True

        # Upload second image
        img_bytes2 = create_test_image()
        response2 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("second.jpg", img_bytes2, "image/jpeg")}
        )

        assert response2.status_code == 201
        data2 = response2.json()
        assert data2["is_primary"] is False
        assert data2["sort_order"] == 1

    def test_upload_image_validates_file_type(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir
    ):
        """Test that only valid image types are accepted"""
        # Try to upload a text file
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("test.txt", text_file, "text/plain")}
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_image_validates_file_size(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        monkeypatch
    ):
        """Test file size validation"""
        # Mock a small max upload size
        from app import config
        monkeypatch.setattr(config.settings, "MAX_UPLOAD_SIZE", 100)  # 100 bytes

        # Create an image larger than the limit
        img_bytes = create_test_image(1000, 1000)

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("large.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 400
        assert "exceeds maximum allowed size" in response.json()["detail"]

    def test_upload_image_extracts_dimensions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir
    ):
        """Test that image dimensions are extracted correctly"""
        img_bytes = create_test_image(1920, 1080)

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("hd.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["width"] == 1920
        assert data["height"] == 1080

    def test_upload_image_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch,
        mock_upload_dir
    ):
        """Test upload without authentication"""
        img_bytes = create_test_image()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 403

    def test_upload_image_wrong_owner(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        mock_upload_dir
    ):
        """Test upload to another user's watch"""
        img_bytes = create_test_image()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers2,
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code == 404


class TestListImages:
    """Test image listing endpoint"""

    def test_list_images_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test listing images for a watch"""
        # Upload two images
        for i in range(2):
            img_bytes = create_test_image()
            client.post(
                f"/api/v1/watches/{test_watch.id}/images",
                headers=auth_headers,
                files={"file": (f"test{i}.jpg", img_bytes, "image/jpeg")}
            )

        # List images
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["file_name"] == "test0.jpg"
        assert data[1]["file_name"] == "test1.jpg"

    def test_list_images_sorted_by_sort_order(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test that images are sorted by sort_order"""
        # Upload images
        for i in range(3):
            img_bytes = create_test_image()
            client.post(
                f"/api/v1/watches/{test_watch.id}/images",
                headers=auth_headers,
                files={"file": (f"img{i}.jpg", img_bytes, "image/jpeg")}
            )

        # Get images
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers
        )

        data = response.json()
        assert data[0]["sort_order"] == 0
        assert data[1]["sort_order"] == 1
        assert data[2]["sort_order"] == 2

    def test_list_images_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test listing images without authentication"""
        response = client.get(f"/api/v1/watches/{test_watch.id}/images")
        assert response.status_code == 403

    def test_list_images_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test listing images when none exist"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []


class TestUpdateImage:
    """Test image update endpoint"""

    def test_update_image_set_primary(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test setting an image as primary"""
        # Upload two images
        img1 = create_test_image()
        img2 = create_test_image()

        r1 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img1.jpg", img1, "image/jpeg")}
        )
        r2 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img2.jpg", img2, "image/jpeg")}
        )

        img1_id = r1.json()["id"]
        img2_id = r2.json()["id"]

        # Set second image as primary
        response = client.patch(
            f"/api/v1/watches/{test_watch.id}/images/{img2_id}",
            headers=auth_headers,
            json={"is_primary": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_primary"] is True

        # Verify first image is no longer primary
        img1_db = test_db.query(WatchImage).filter(WatchImage.id == img1_id).first()
        assert img1_db.is_primary is False

    def test_update_image_unsets_other_primary(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test that setting an image as primary unsets others"""
        # Upload three images
        image_ids = []
        for i in range(3):
            img = create_test_image()
            r = client.post(
                f"/api/v1/watches/{test_watch.id}/images",
                headers=auth_headers,
                files={"file": (f"img{i}.jpg", img, "image/jpeg")}
            )
            image_ids.append(r.json()["id"])

        # Set third image as primary
        client.patch(
            f"/api/v1/watches/{test_watch.id}/images/{image_ids[2]}",
            headers=auth_headers,
            json={"is_primary": True}
        )

        # Check that only third image is primary
        images = test_db.query(WatchImage).filter(
            WatchImage.watch_id == test_watch.id
        ).all()

        primary_count = sum(1 for img in images if img.is_primary)
        assert primary_count == 1

        primary_img = next(img for img in images if img.is_primary)
        assert str(primary_img.id) == image_ids[2]

    def test_update_image_change_sort_order(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir
    ):
        """Test changing image sort order"""
        # Upload image
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Update sort order
        response = client.patch(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers,
            json={"sort_order": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sort_order"] == 5

    def test_update_image_auto_promotes_when_unset(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test auto-promotion when unsetting primary with multiple images"""
        # Upload two images
        img1 = create_test_image()
        img2 = create_test_image()

        r1 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img1.jpg", img1, "image/jpeg")}
        )
        client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img2.jpg", img2, "image/jpeg")}
        )

        img1_id = r1.json()["id"]

        # Unset first image as primary
        response = client.patch(
            f"/api/v1/watches/{test_watch.id}/images/{img1_id}",
            headers=auth_headers,
            json={"is_primary": False}
        )

        assert response.status_code == 200

        # Verify second image was promoted
        images = test_db.query(WatchImage).filter(
            WatchImage.watch_id == test_watch.id
        ).order_by(WatchImage.sort_order).all()

        assert images[0].is_primary is False
        assert images[1].is_primary is True

    def test_update_image_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        mock_upload_dir,
        auth_headers: dict
    ):
        """Test updating another user's image"""
        # Upload image as user 1
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Try to update as user 2
        response = client.patch(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers2,
            json={"is_primary": True}
        )

        assert response.status_code == 404

    def test_update_image_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test updating non-existent image"""
        response = client.patch(
            f"/api/v1/watches/{test_watch.id}/images/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
            json={"is_primary": True}
        )

        assert response.status_code == 404


class TestDeleteImage:
    """Test image deletion endpoint"""

    def test_delete_image_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test successful image deletion"""
        # Upload image
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Delete image
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify image is deleted from database
        img_db = test_db.query(WatchImage).filter(WatchImage.id == image_id).first()
        assert img_db is None

    def test_delete_image_auto_promotes_next_primary(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test that deleting primary image promotes the next one"""
        # Upload two images
        img1 = create_test_image()
        img2 = create_test_image()

        r1 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img1.jpg", img1, "image/jpeg")}
        )
        r2 = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img2.jpg", img2, "image/jpeg")}
        )

        img1_id = r1.json()["id"]
        img2_id = r2.json()["id"]

        # Delete first image (which is primary)
        client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{img1_id}",
            headers=auth_headers
        )

        # Verify second image is now primary
        img2_db = test_db.query(WatchImage).filter(WatchImage.id == img2_id).first()
        assert img2_db.is_primary is True

    def test_delete_image_removes_database_record(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test that delete endpoint removes database record"""
        # Upload image
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Delete image
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify database record is deleted
        from app.models.watch_image import WatchImage
        deleted_img = test_db.query(WatchImage).filter(
            WatchImage.id == image_id
        ).first()
        assert deleted_img is None

    def test_delete_image_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test deleting non-existent image"""
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/images/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_image_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        mock_upload_dir,
        auth_headers: dict
    ):
        """Test deleting another user's image"""
        # Upload image as user 1
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Try to delete as user 2
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers2
        )

        assert response.status_code == 404

    def test_delete_image_removes_from_database(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        mock_upload_dir,
        test_db: Session
    ):
        """Test database record removal"""
        # Upload image
        img = create_test_image()
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("img.jpg", img, "image/jpeg")}
        )
        image_id = r.json()["id"]

        # Verify record exists
        img_before = test_db.query(WatchImage).filter(WatchImage.id == image_id).first()
        assert img_before is not None

        # Delete image
        client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}",
            headers=auth_headers
        )

        # Verify record is gone
        img_after = test_db.query(WatchImage).filter(WatchImage.id == image_id).first()
        assert img_after is None
