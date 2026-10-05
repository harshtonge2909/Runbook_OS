import os
from app import create_app, db
from app.models.user import User
from app.models.runbook import Runbook, Step
from app.models.execution import Execution
from app.models.audit import AuditLog

app = create_app(os.getenv("FLASK_ENV", "development"))


def do_init_db():
    """Create all database tables in PostgreSQL."""
    with app.app_context():
        db.create_all()
        print("PostgreSQL tables created successfully.")


def do_seed_db():
    """Seed initial demo users, runbooks, and audit logs."""
    with app.app_context():
        db.create_all()

        # Create demo admin user if not exists
        admin = User.query.filter_by(email="admin@runbookos.dev").first()
        if not admin:
            admin = User(
                name="SRE Admin",
                email="admin@runbookos.dev",
                role="Admin",
                status="active"
            )
            admin.set_password("Admin@123456")
            db.session.add(admin)

        # Create demo engineer user if not exists
        engineer = User.query.filter_by(email="engineer@runbookos.dev").first()
        if not engineer:
            engineer = User(
                name="DevOps Engineer",
                email="engineer@runbookos.dev",
                role="Engineer",
                status="active"
            )
            engineer.set_password("Engineer@123456")
            db.session.add(engineer)

        db.session.commit()

        # Create sample operational runbook if none exists
        if Runbook.query.count() == 0:
            rb1 = Runbook(
                title="PostgreSQL High Memory & Connection Spike Triage",
                description="Standard operational procedure for diagnosing and mitigating connection pool exhaustion and memory spikes on production PostgreSQL databases.",
                version=1,
                status="active",
                created_by_id=admin.id
            )
            db.session.add(rb1)
            db.session.flush()

            steps_data = [
                {
                    "order": 1,
                    "title": "Check Active Connection Count and State",
                    "instructions": "SELECT state, count(*) FROM pg_stat_activity GROUP BY state ORDER BY count(*) DESC;\n-- Also verify max_connections limit:\nSHOW max_connections;",
                    "expected_outcome": "Identify if connection count is nearing max_connections (typically > 85%) or if queries are stuck in 'idle in transaction'."
                },
                {
                    "order": 2,
                    "title": "Identify Long-Running or Blocking Queries",
                    "instructions": "SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '2 minutes' AND state != 'idle';",
                    "expected_outcome": "List of offending query PIDs causing locks or high CPU/memory consumption."
                },
                {
                    "order": 3,
                    "title": "Terminate Problematic Backend Processes",
                    "instructions": "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid IN (<LIST_OF_OFFENDING_PIDS>);",
                    "expected_outcome": "Terminated queries return 'true', free up connection slots, and release system memory."
                },
                {
                    "order": 4,
                    "title": "Verify Connection Pool Recovery",
                    "instructions": "SELECT count(*) FROM pg_stat_activity;\n-- Monitor memory utilization on the database host.",
                    "expected_outcome": "Total connections drop back below safety threshold (e.g. < 50 connections) and memory stabilizes."
                }
            ]

            for s in steps_data:
                step = Step(
                    runbook_id=rb1.id,
                    order=s["order"],
                    title=s["title"],
                    instructions=s["instructions"],
                    expected_outcome=s["expected_outcome"]
                )
                db.session.add(step)

            # Sample runbook 2
            rb2 = Runbook(
                title="Kubernetes Pod CrashLoopBackOff Remediation",
                description="Procedure to diagnose and recover microservices stuck in CrashLoopBackOff within production Kubernetes clusters.",
                version=1,
                status="active",
                created_by_id=engineer.id
            )
            db.session.add(rb2)
            db.session.flush()

            steps_data_2 = [
                {
                    "order": 1,
                    "title": "Inspect Pod Status & Event Log",
                    "instructions": "kubectl get pods -n production -l app=service-api\nkubectl describe pod <POD_NAME> -n production",
                    "expected_outcome": "Look under 'Events' for Exit Code (e.g., OOMKilled 137, Command Failed 1, Missing Config 128)."
                },
                {
                    "order": 2,
                    "title": "Fetch Previous Container Logs",
                    "instructions": "kubectl logs <POD_NAME> -n production --previous --tail=100",
                    "expected_outcome": "Reveal the stack trace, missing environment variable, or startup panic message."
                },
                {
                    "order": 3,
                    "title": "Rollback Deployment to Last Known Good Revision",
                    "instructions": "kubectl rollout undo deployment/service-api -n production\nkubectl rollout status deployment/service-api -n production",
                    "expected_outcome": "Deployment successfully rolls back to previous replica set and pods return to Running state (1/1)."
                }
            ]

            for s in steps_data_2:
                step = Step(
                    runbook_id=rb2.id,
                    order=s["order"],
                    title=s["title"],
                    instructions=s["instructions"],
                    expected_outcome=s["expected_outcome"]
                )
                db.session.add(step)

            db.session.commit()
            print("Database seeded with demo users, runbooks, and procedural steps.")
        else:
            print("Database already contains runbooks.")


@app.cli.command("init-db")
def init_db():
    do_init_db()


@app.cli.command("seed-db")
def seed_db():
    do_seed_db()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "init-db":
            do_init_db()
        elif cmd == "seed-db":
            do_seed_db()
        else:
            print(f"Unknown command: {cmd}. Usage: python run.py [init-db | seed-db]")
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)

