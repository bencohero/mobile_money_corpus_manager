"""Reproducible C.1 benchmark; run only against the dedicated test database."""
import argparse
import statistics
import time
import tracemalloc
from datetime import datetime, timedelta

from sqlalchemy import event

from app.db import SessionLocal, engine
from app.models import Participant, Recording, Transcription, Utterance, Workshop
from app.time_utils import utc_now


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * fraction))]


def bounded_audio_benchmark(megabytes=64):
    block = b"0" * (1024 * 1024)
    tracemalloc.start()
    started = time.perf_counter()
    consumed = sum(len(block) for _ in range(megabytes))
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    return consumed, elapsed, peak


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="1000,10000,100000")
    args = parser.parse_args()
    sizes = [int(value) for value in args.sizes.split(",") if value]
    consumed, elapsed, peak = bounded_audio_benchmark()
    print(f"audio_synthetic_bytes={consumed},audio_seconds={elapsed:.6f},audio_mib_s={consumed / 1024 / 1024 / elapsed:.2f},audio_python_peak_kib={peak / 1024:.1f}")
    with SessionLocal() as db:
        workshop = db.query(Workshop).first()
        participant = db.query(Participant).first()
        utterance = db.query(Utterance).first()
        if not all((workshop, participant, utterance)):
            raise SystemExit("test database requires seeded workshop, participant and utterance")
        print("size,page_p50_ms,page_p95_ms,count_p50_ms,count_p95_ms,sql_page,sql_count,python_peak_kib")
        for size in sizes:
            started = time.perf_counter()
            participant_rows = [Participant(workshop_id=workshop.id, participant_code=f"BENCH_{size}_{i}", language="mos", language_code="MOS", consent_obtained=True) for i in range(max(2, min(250, (size + 998) // 999)))]
            db.add_all(participant_rows); db.flush()
            participant_ids = [row.id for row in participant_rows]
            rows = [{"workshop_id": workshop.id, "participant_id": participant_ids[i % len(participant_ids)], "utterance_id": utterance.id,
                     "audio_id": f"BENCH_{size}_{i}", "condition": "CLEAN", "raw_object": f"bench/{size}/{i}.raw",
                     "wav_object": f"bench/{size}/{i}.wav", "status": "RECORDED", "sync_status": "READY",
                     "created_at": utc_now() - timedelta(seconds=size - i), "take_number": (i // len(participant_ids)) + 1} for i in range(size)]
            db.bulk_insert_mappings(Recording, rows)
            db.flush()
            db.commit()
            page_times, count_times = [], []
            page_sql = count_sql = 0
            for _ in range(5):
                counters = {"page": 0, "count": 0}
                def before(_conn, _cursor, statement, _parameters, _context, _executemany):
                    if "count" in statement.lower(): counters["count"] += 1
                    else: counters["page"] += 1
                event.listen(engine, "before_cursor_execute", before)
                try:
                    query = db.query(Recording).filter(Recording.sync_status == "READY").order_by(Recording.created_at.desc(), Recording.id.desc())
                    t = time.perf_counter(); query.offset(100).limit(50).all(); page_times.append((time.perf_counter() - t) * 1000)
                    t = time.perf_counter(); query.count(); count_times.append((time.perf_counter() - t) * 1000)
                finally:
                    event.remove(engine, "before_cursor_execute", before)
                page_sql += counters["page"]; count_sql += counters["count"]
            tracemalloc.start()
            [row["audio_id"] for row in rows[: min(size, 1000)]]
            _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
            print(f"{size},{percentile(page_times, .50):.3f},{percentile(page_times, .95):.3f},{percentile(count_times, .50):.3f},{percentile(count_times, .95):.3f},{page_sql // 5},{count_sql // 5},{peak // 1024}")
            db.query(Recording).filter(Recording.audio_id.like(f"BENCH_{size}_%")).delete(synchronize_session=False)
            db.query(Participant).filter(Participant.id.in_(participant_ids)).delete(synchronize_session=False)
            db.commit()
            print(f"completed_{size}_seconds={(time.perf_counter() - started):.3f}")


if __name__ == "__main__":
    main()
