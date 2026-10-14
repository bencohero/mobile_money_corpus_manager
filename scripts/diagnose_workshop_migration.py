"""Read-only pre-migration workshop attribution diagnostic."""
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.effective_database_url)
with engine.connect() as conn:
    for label, query in {
        "workshops": "SELECT count(*) FROM workshops" if conn.dialect.has_table(conn, "workshops") else "SELECT 0",
        "workshop_codes": "SELECT count(*) FROM workshop_codes",
        "participants_without_workshop": "SELECT count(*) FROM participants WHERE workshop_id IS NULL" if conn.dialect.has_table(conn, "participants") and any(c['name']=='workshop_id' for c in conn.dialect.get_columns(conn, 'participants')) else "SELECT count(*) FROM participants",
        "recordings_without_workshop": "SELECT count(*) FROM recordings WHERE workshop_id IS NULL" if conn.dialect.has_table(conn, "recordings") and any(c['name']=='workshop_id' for c in conn.dialect.get_columns(conn, 'recordings')) else "SELECT count(*) FROM recordings",
        "participant_recording_mismatches": "SELECT count(*) FROM recordings r JOIN participants p ON p.id=r.participant_id WHERE r.workshop_id IS DISTINCT FROM p.workshop_id" if conn.dialect.has_table(conn, "recordings") and any(c['name']=='workshop_id' for c in conn.dialect.get_columns(conn, 'recordings')) else "SELECT 0",
        "disabled_workshops": "SELECT count(*) FROM workshops WHERE NOT is_active" if conn.dialect.has_table(conn, "workshops") else "SELECT 0",
    }.items():
        print(f"{label}: {conn.execute(text(query)).scalar_one()}")
