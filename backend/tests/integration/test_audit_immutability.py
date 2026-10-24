import pytest
from app.adapters.db.session import SessionLocal
from app.adapters.db.models import AuditLog
from app.adapters.db.audit import record_audit


def test_audit_hash_chaining_and_immutability():
    db = SessionLocal()
    try:
        # 1. Record two consecutive audit entries
        log1 = record_audit(
            db=db,
            action="test_action_1",
            entity_type="test_entity",
            entity_id="id-001",
            actor_id="u-admin",
            details={"step": 1},
        )
        assert log1.hash is not None
        assert len(log1.hash) == 64

        log2 = record_audit(
            db=db,
            action="test_action_2",
            entity_type="test_entity",
            entity_id="id-002",
            actor_id="u-admin",
            details={"step": 2},
        )
        assert log2.hash is not None
        assert len(log2.hash) == 64
        # Verify hash chaining
        assert log2.prev_hash == log1.hash

        # 2. Verify immutability: attempting UPDATE must raise RuntimeError
        with pytest.raises(RuntimeError, match="append-only and cannot be modified"):
            log1.action = "tampered_action"
            db.commit()

        db.rollback()

        # 3. Verify immutability: attempting DELETE must raise RuntimeError
        with pytest.raises(RuntimeError, match="append-only and cannot be deleted"):
            db.delete(log2)
            db.commit()

        db.rollback()

    finally:
        db.close()
