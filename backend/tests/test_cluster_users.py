import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from services.cluster_users import run_user_clustering, EMBEDDING_UPDATE_INTERVAL_DAYS, NUM_CLUSTERS
from models.user import User, UserActivity, Activity
from models.cluster import Cluster, UserClusterAssociation, ClusterDestination


class TestRunUserClustering:
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.query.return_value = session
        session.filter.return_value = session
        session.filter_by.return_value = session
        session.all.return_value = []
        session.first.return_value = None
        session.flush.return_value = None
        session.commit.return_value = None
        session.rollback.return_value = None
        session.delete.return_value = Mock()
        return session

    @pytest.fixture
    def mock_users_needing_update(self):
        """Create mock users that need embedding updates."""
        users = []
        for i in range(3):
            user = Mock(spec=User)
            user.id = i + 1
            user.embedding = None
            user.last_embedding_update = None
            users.append(user)
        return users

    @pytest.fixture
    def mock_users_with_embeddings(self):
        """Create mock users with existing embeddings."""
        users = []
        for i in range(5):
            user = Mock()
            user.id = i + 1
            user.embedding = [0.1, 0.2, 0.3] if i % 2 == 0 else [0.4, 0.5, 0.6]
            users.append(user)
        return users

    @patch('services.cluster_users.embed_user')
    @patch('services.cluster_users.cluster_users')
    @patch('services.cluster_users.compute_top_destinations_for_cluster')
    def test_run_user_clustering_success(self, mock_compute_dest, mock_cluster_users, 
                                       mock_embed_user, mock_session, mock_users_needing_update,
                                       mock_users_with_embeddings):
        """Test successful user clustering execution."""
        # Setup mocks
        mock_session.query.return_value.filter.return_value.all.return_value = mock_users_needing_update
        mock_embed_user.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Mock users with embeddings for clustering
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            mock_users_needing_update,  # First call for users needing update
            mock_users_with_embeddings  # Second call for users with embeddings
        ]
        
        # Mock clustering results
        mock_cluster_users.return_value = {1: 0, 2: 1, 3: 0, 4: 1, 5: 0}
        
        # Mock existing clusters
        mock_clusters = [Mock(id=i+10, name=f"KMeans Cluster {i}", algorithm="KMeans") for i in range(NUM_CLUSTERS)]
        mock_session.query.return_value.filter_by.return_value.first.side_effect = mock_clusters
        
        # Mock top destinations
        mock_compute_dest.return_value = [
            {"destination_id": 1, "popularity_score": 85.5},
            {"destination_id": 2, "popularity_score": 72.3}
        ]
        
        # Execute function
        run_user_clustering(mock_session)
        
        # Verify embedding generation was called for each user needing update
        assert mock_embed_user.call_count == len(mock_users_needing_update)
        for user in mock_users_needing_update:
            mock_embed_user.assert_any_call(user.id, mock_session)
            assert user.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
            assert user.last_embedding_update is not None
        
        # Verify clustering was called
        mock_cluster_users.assert_called_once()
        
        # Verify session operations
        mock_session.flush.assert_called()
        mock_session.commit.assert_called_once()

    @patch('services.cluster_users.embed_user')
    def test_run_user_clustering_no_users_needing_update(self, mock_embed_user, mock_session):
        """Test when no users need embedding updates."""
        # No users need updates
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        # Mock users with embeddings
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # No users needing update
            []   # No users with embeddings
        ]
        
        # Execute function - should not crash
        run_user_clustering(mock_session)
        
        # Verify embed_user was not called
        mock_embed_user.assert_not_called()
        
        # Session should still commit (even if no changes)
        mock_session.commit.assert_called_once()

    @patch('services.cluster_users.embed_user')
    def test_run_user_clustering_no_users_with_embeddings(self, mock_embed_user, mock_session):
        """Test when no users have embeddings for clustering."""
        # Some users need updates but none end up with embeddings
        mock_users = [Mock(id=1, embedding=None), Mock(id=2, embedding=None)]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            mock_users,  # Users needing update
            []           # No users with embeddings after update
        ]
        
        # embed_user returns None (insufficient data)
        mock_embed_user.return_value = None
        
        # Execute function
        run_user_clustering(mock_session)
        
        # Verify embeddings remained None
        for user in mock_users:
            assert user.embedding is None

    @patch('services.cluster_users.embed_user')
    @patch('services.cluster_users.cluster_users')
    def test_run_user_clustering_creates_missing_clusters(self, mock_cluster_users, 
                                                         mock_embed_user, mock_session):
        """Test that missing clusters are created."""
        # Mock users with embeddings
        mock_users_with_embeddings = [Mock(id=i+1, embedding=[0.1, 0.2]) for i in range(3)]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # No users needing update
            mock_users_with_embeddings  # Users with embeddings
        ]
        
        # Mock clustering results
        mock_cluster_users.return_value = {1: 0, 2: 1, 3: 2}
        
        # No existing clusters
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Mock new cluster creation
        def mock_cluster_constructor(name, algorithm):
            cluster = Mock()
            cluster.name = name
            cluster.algorithm = algorithm
            cluster.id = hash(name) % 1000  # Simple mock ID
            return cluster
        
        with patch('services.cluster_users.Cluster', side_effect=mock_cluster_constructor):
            run_user_clustering(mock_session)
        
        # Verify clusters were added
        assert mock_session.add.call_count >= NUM_CLUSTERS

    @patch('services.cluster_users.embed_user')
    def test_run_user_clustering_handles_embed_failure(self, mock_embed_user, mock_session):
        """Test handling when embedding generation fails for some users."""
        mock_users = [Mock(id=1, embedding=None), Mock(id=2, embedding=None)]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            mock_users,  # Users needing update
            []           # No users with embeddings after failed attempts
        ]
        
        # First call succeeds, second fails
        mock_embed_user.side_effect = [[0.1, 0.2, 0.3], None]
        
        run_user_clustering(mock_session)
        
        # First user should have embedding, second should not
        assert mock_users[0].embedding == [0.1, 0.2, 0.3]
        assert mock_users[1].embedding is None

    @patch('services.cluster_users.embed_user')
    def test_run_user_clustering_exception_handling(self, mock_embed_user, mock_session):
        """Test that exceptions are properly handled with rollback."""
        mock_session.query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            run_user_clustering(mock_session)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @patch('services.cluster_users.embed_user')
    @patch('services.cluster_users.cluster_users')
    @patch('services.cluster_users.compute_top_destinations_for_cluster')
    def test_run_user_clustering_cluster_destinations_update(self, mock_compute_dest, 
                                                           mock_cluster_users, mock_embed_user, 
                                                           mock_session):
        """Test that cluster destinations are properly updated."""
        # Mock setup
        mock_users_with_embeddings = [Mock(id=i+1, embedding=[0.1, 0.2]) for i in range(3)]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # No users needing update
            mock_users_with_embeddings  # Users with embeddings
        ]
        
        mock_cluster_users.return_value = {1: 0, 2: 0, 3: 1}
        
        # Mock existing clusters
        mock_clusters = [Mock(id=10+i, name=f"KMeans Cluster {i}") for i in range(NUM_CLUSTERS)]
        mock_session.query.return_value.filter_by.return_value.first.side_effect = mock_clusters
        
        # Mock destination computation
        mock_compute_dest.return_value = [
            {"destination_id": 101, "popularity_score": 95.0},
            {"destination_id": 102, "popularity_score": 87.5}
        ]
        
        with patch('services.cluster_users.ClusterDestination') as mock_cluster_dest_class:
            run_user_clustering(mock_session)
        
        # Verify destinations were computed for each unique cluster
        unique_cluster_ids = {10, 11}  # Based on mock clustering results (clusters 0 and 1)
        assert mock_compute_dest.call_count == len(unique_cluster_ids)
        
        # Verify old cluster destinations were deleted
        mock_session.query.return_value.filter_by.return_value.delete.assert_called()

    def test_embedding_update_interval_configuration(self):
        """Test that the embedding update interval is properly configured."""
        assert EMBEDDING_UPDATE_INTERVAL_DAYS == 7
        assert NUM_CLUSTERS == 5

    @patch('services.cluster_users.embed_user')
    @patch('services.cluster_users.cluster_users')
    def test_run_user_clustering_insufficient_users_for_clustering(self, mock_cluster_users, 
                                                                  mock_embed_user, mock_session):
        """Test clustering when there are fewer users than desired clusters."""
        # Only 2 users with embeddings, but NUM_CLUSTERS = 5
        mock_users_with_embeddings = [Mock(id=1, embedding=[0.1]), Mock(id=2, embedding=[0.2])]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # No users needing update
            mock_users_with_embeddings  # Users with embeddings
        ]
        
        # cluster_users should handle this case by assigning all to cluster 0
        mock_cluster_users.return_value = {1: 0, 2: 0}
        
        run_user_clustering(mock_session)
        
        # Verify clustering was called despite insufficient users
        mock_cluster_users.assert_called_once()

    @patch('services.cluster_users.logger')
    def test_logging_behavior(self, mock_logger, mock_session):
        """Test that appropriate log messages are generated."""
        mock_session.query.return_value.filter.return_value.all.return_value = []
        
        run_user_clustering(mock_session)
        
        # Verify logging calls
        mock_logger.info.assert_any_call("Starting scheduled user clustering process.")
        mock_logger.warning.assert_any_call("No users with embeddings found. Skipping clustering.")