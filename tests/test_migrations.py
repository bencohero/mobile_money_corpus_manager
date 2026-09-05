import os
from sqlalchemy import create_engine, inspect, text
def test_migrated_schema_matches_expected():
    engine=create_engine(os.environ["DATABASE_URL"])
    names=set(inspect(engine).get_table_names())
    assert {"users","participants","utterances","recordings","transcriptions","audit_logs","alembic_version"} <= names
    columns={c["name"] for c in inspect(engine).get_columns("recordings")}
    assert {"sync_status","raw_sha256","wav_sha256","finalized_at"} <= columns
    indexes={i["name"] for i in inspect(engine).get_indexes("recordings")}
    assert "ix_recordings_sync_status" in indexes
    with engine.connect() as conn:
        assert conn.execute(text("select version_num from alembic_version")).scalar() == "0002_p0a_recording_sync"
