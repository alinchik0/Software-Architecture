# migrations/versions/0001_initial.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(), nullable=False), sa.Column("username", sa.String(), nullable=False), sa.Column("password_hash", sa.String(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()), sa.Column("profile_data", postgresql.JSONB(), server_default="{}"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.create_table("playlists", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(), nullable=False), sa.Column("description", sa.Text()), sa.Column("is_public", sa.Boolean(), server_default="false"), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_playlists_owner_public", "playlists", ["owner_id", "is_public"])
    op.create_table("playlist_tracks", sa.Column("playlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True), sa.Column("spotify_track_id", sa.String(), primary_key=True), sa.Column("position", sa.Integer(), nullable=False), sa.Column("added_at", sa.DateTime(), server_default=sa.func.now()))
    op.create_index("ix_playlist_tracks_playlist_id", "playlist_tracks", ["playlist_id"])
    op.create_table("kafka_events", sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("topic", sa.String()), sa.Column("processed_at", sa.DateTime(), server_default=sa.func.now()), sa.UniqueConstraint("topic", "event_id", name="uq_kafka_events_topic_event_id"))

def downgrade() -> None:
    op.drop_table("kafka_events")
    op.drop_index("ix_playlist_tracks_playlist_id", table_name="playlist_tracks")
    op.drop_table("playlist_tracks")
    op.drop_index("ix_playlists_owner_public", table_name="playlists")
    op.drop_table("playlists")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
