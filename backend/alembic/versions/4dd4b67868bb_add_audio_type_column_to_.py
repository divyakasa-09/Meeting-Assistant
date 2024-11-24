"""Add audio_type column to TranscriptSegment

Revision ID: 4dd4b67868bb
Revises: a4efdf99f07f
Create Date: 2024-11-16 12:22:13.011266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4dd4b67868bb'
down_revision: Union[str, None] = 'a4efdf99f07f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('action_items', 'status',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('action_items', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.create_index(op.f('ix_action_items_created_at'), 'action_items', ['created_at'], unique=False)
    op.drop_constraint('action_items_meeting_id_fkey', 'action_items', type_='foreignkey')
    op.create_foreign_key(None, 'action_items', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    op.alter_column('follow_up_questions', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.create_index(op.f('ix_follow_up_questions_created_at'), 'follow_up_questions', ['created_at'], unique=False)
    op.drop_constraint('follow_up_questions_meeting_id_fkey', 'follow_up_questions', type_='foreignkey')
    op.create_foreign_key(None, 'follow_up_questions', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_meetings_start_time'), 'meetings', ['start_time'], unique=False)
    op.alter_column('summaries', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.create_index(op.f('ix_summaries_created_at'), 'summaries', ['created_at'], unique=False)
    op.drop_constraint('summaries_meeting_id_fkey', 'summaries', type_='foreignkey')
    op.create_foreign_key(None, 'summaries', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    op.alter_column('transcript_segments', 'timestamp',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.create_index(op.f('ix_transcript_segments_audio_type'), 'transcript_segments', ['audio_type'], unique=False)
    op.create_index(op.f('ix_transcript_segments_timestamp'), 'transcript_segments', ['timestamp'], unique=False)
    op.drop_constraint('transcript_segments_meeting_id_fkey', 'transcript_segments', type_='foreignkey')
    op.create_foreign_key(None, 'transcript_segments', 'meetings', ['meeting_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'transcript_segments', type_='foreignkey')
    op.create_foreign_key('transcript_segments_meeting_id_fkey', 'transcript_segments', 'meetings', ['meeting_id'], ['id'])
    op.drop_index(op.f('ix_transcript_segments_timestamp'), table_name='transcript_segments')
    op.drop_index(op.f('ix_transcript_segments_audio_type'), table_name='transcript_segments')
    op.alter_column('transcript_segments', 'timestamp',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_constraint(None, 'summaries', type_='foreignkey')
    op.create_foreign_key('summaries_meeting_id_fkey', 'summaries', 'meetings', ['meeting_id'], ['id'])
    op.drop_index(op.f('ix_summaries_created_at'), table_name='summaries')
    op.alter_column('summaries', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_index(op.f('ix_meetings_start_time'), table_name='meetings')
    op.drop_constraint(None, 'follow_up_questions', type_='foreignkey')
    op.create_foreign_key('follow_up_questions_meeting_id_fkey', 'follow_up_questions', 'meetings', ['meeting_id'], ['id'])
    op.drop_index(op.f('ix_follow_up_questions_created_at'), table_name='follow_up_questions')
    op.alter_column('follow_up_questions', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_constraint(None, 'action_items', type_='foreignkey')
    op.create_foreign_key('action_items_meeting_id_fkey', 'action_items', 'meetings', ['meeting_id'], ['id'])
    op.drop_index(op.f('ix_action_items_created_at'), table_name='action_items')
    op.alter_column('action_items', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('action_items', 'status',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
