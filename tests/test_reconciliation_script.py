from pathlib import Path


SOURCE = Path("scripts/reconcile_participant_registration_schema.py").read_text()


def test_reconciliation_is_guarded_and_preserves_workshop_backup():
    assert "RECONCILE-PARTICIPANT-REGISTRATION" in SOURCE
    assert 'parser.add_argument("--dry-run"' in SOURCE
    assert "workshop_codes_reconcile_backup" in SOURCE
    assert "participant_login_number_seq" in SOURCE
    assert "alembic_version" in SOURCE
