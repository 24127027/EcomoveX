import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, create_autospec

# IMPORTANT: Add backend to path BEFORE importing from services
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# ===================================================================
# CRITICAL: Mock circular imports BEFORE any other imports
# ===================================================================
# Create a complete mock module for cluster_users
mock_cluster_users = MagicMock()
mock_cluster_users.get_user_cluster_id = MagicMock(return_value=10)

# Inject the mock into sys.modules to prevent real import
sys.modules['services.cluster.cluster_users'] = mock_cluster_users

# Now safe to import
from sqlalchemy.orm import Session
from services.recommendation_service import filter_destinations_by_user_cluster


class TestFilterDestinationsByUserCluster:
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        return session

    def test_successful_filtering(self, mock_session):
        """
        Test Case 1: Kiểm tra lọc destination_id thành công
        Khi có danh sách destination_ids hợp lệ và DB trả về subset
        thuộc về cluster_id của user.
        """
        # Arrange: Setup input data
        destination_ids = [1, 2, 3, 4, 5]
        user_id = 100
        cluster_id = 10
        
        # Mock get_user_cluster_id để trả về cluster_id
        # Patch at the point of use (trong recommendation_service module)
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = cluster_id
            
            # Mock DB response - chỉ trả về ID 1, 3, 5 thuộc cluster 10
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [
                (1,),  # Mỗi row là tuple chứa destination_id
                (3,),
                (5,)
            ]
            
            # Mock session.execute() để trả về mock_result
            mock_session.execute.return_value = mock_result
            
            # Act: Gọi hàm cần test
            filtered_ids = filter_destinations_by_user_cluster(
                destination_ids=destination_ids,
                user_id=user_id,
                session=mock_session
            )
            
            # Assert: Xác minh kết quả
            assert filtered_ids == [1, 3, 5], "Should return only IDs belonging to user's cluster"
            
            # Verify get_user_cluster_id was called with correct user_id
            mock_get_cluster.assert_called_once_with(user_id, mock_session)
            
            # Verify session.execute was called once
            mock_session.execute.assert_called_once()

    def test_empty_input_list(self, mock_session):
        """
        Test Case 2: Kiểm tra với danh sách đầu vào rỗng
        Khi destination_ids = [], hàm phải trả về [] mà không gọi DB.
        """
        # Arrange: Setup input data with empty list
        destination_ids = []
        user_id = 100
        
        # Act: Gọi hàm với danh sách rỗng
        filtered_ids = filter_destinations_by_user_cluster(
            destination_ids=destination_ids,
            user_id=user_id,
            session=mock_session
        )
        
        # Assert: Xác minh kết quả là danh sách rỗng
        assert filtered_ids == [], "Should return empty list when input is empty"
        
        # Verify session.execute was NOT called (optimization)
        mock_session.execute.assert_not_called()

    def test_user_without_cluster(self, mock_session):
        """
        Test Case 3: Kiểm tra khi user không có cluster
        """
        # Arrange
        destination_ids = [1, 2, 3]
        user_id = 999  # User không có cluster
        
        # Mock get_user_cluster_id trả về None
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = None
            
            # Act
            filtered_ids = filter_destinations_by_user_cluster(
                destination_ids=destination_ids,
                user_id=user_id,
                session=mock_session
            )
            
            # Assert
            assert filtered_ids == [], "Should return empty list when user has no cluster"
            
            # Verify get_user_cluster_id was called
            mock_get_cluster.assert_called_once_with(user_id, mock_session)
            
            # Verify session.execute was NOT called
            mock_session.execute.assert_not_called()

    def test_no_matching_destinations(self, mock_session):
        """
        Test Case 4: Kiểm tra khi không có destination nào khớp cluster của user
        """
        # Arrange
        destination_ids = [1, 2, 3]
        user_id = 100
        cluster_id = 10
        
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = cluster_id
            
            # Mock DB trả về empty result
            mock_result = MagicMock()
            mock_result.fetchall.return_value = []  # Không có kết quả
            mock_session.execute.return_value = mock_result
            
            # Act
            filtered_ids = filter_destinations_by_user_cluster(
                destination_ids=destination_ids,
                user_id=user_id,
                session=mock_session
            )
            
            # Assert
            assert filtered_ids == [], "Should return empty list when no destinations match"
            mock_session.execute.assert_called_once()

    def test_all_destinations_match(self, mock_session):
        """
        Test Case 5: Kiểm tra khi tất cả destination đều thuộc cluster của user
        """
        # Arrange
        destination_ids = [10, 20, 30]
        user_id = 100
        cluster_id = 5
        
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = cluster_id
            
            # Mock DB trả về tất cả IDs
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [(10,), (20,), (30,)]
            mock_session.execute.return_value = mock_result
            
            # Act
            filtered_ids = filter_destinations_by_user_cluster(
                destination_ids=destination_ids,
                user_id=user_id,
                session=mock_session
            )
            
            # Assert
            assert filtered_ids == [10, 20, 30], "Should return all IDs when all match"
            assert len(filtered_ids) == len(destination_ids)

    def test_database_error_handling(self, mock_session):
        """
        Test Case 6: Kiểm tra xử lý lỗi từ database
        """
        # Arrange
        destination_ids = [1, 2, 3]
        user_id = 100
        cluster_id = 5
        
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = cluster_id
            
            # Mock DB raise exception
            mock_session.execute.side_effect = Exception("Database connection error")
            
            # Act & Assert: Kiểm tra xem hàm có raise exception hay return []
            try:
                filtered_ids = filter_destinations_by_user_cluster(
                    destination_ids=destination_ids,
                    user_id=user_id,
                    session=mock_session
                )
                # Nếu hàm trả về [] thay vì raise exception
                assert filtered_ids == [], "Should return empty list on database error"
            except Exception as e:
                # Nếu hàm raise exception
                assert "Database connection error" in str(e), "Should propagate database errors"

    def test_single_destination_filtering(self, mock_session):
        """
        Test Case 7: Kiểm tra với chỉ một destination_id
        """
        # Arrange
        destination_ids = [42]
        user_id = 100
        cluster_id = 3
        
        with patch('services.recommendation_service.get_user_cluster_id') as mock_get_cluster:
            mock_get_cluster.return_value = cluster_id
            
            # Mock DB trả về ID đó
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [(42,)]
            mock_session.execute.return_value = mock_result
            
            # Act
            filtered_ids = filter_destinations_by_user_cluster(
                destination_ids=destination_ids,
                user_id=user_id,
                session=mock_session
            )
            
            # Assert
            assert filtered_ids == [42], "Should handle single ID correctly"
            mock_session.execute.assert_called_once()