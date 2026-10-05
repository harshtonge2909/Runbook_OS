from app.models.user import User
from app.models.runbook import Runbook
from app.models.execution import Execution


def get_dashboard_stats():
    """Calculate real-time operational statistics for the dashboard."""
    total_users = User.query.count()
    total_runbooks = Runbook.query.count()
    active_runbooks = Runbook.query.filter_by(status="active").count()
    inactive_runbooks = Runbook.query.filter_by(status="inactive").count()
    running_executions = Execution.query.filter_by(status="Running").count()
    completed_executions = Execution.query.filter_by(status="Completed").count()

    return {
        "totalUsers": total_users,
        "totalRunbooks": total_runbooks,
        "activeRunbooks": active_runbooks,
        "inactiveRunbooks": inactive_runbooks,
        "runningExecutions": running_executions,
        "completedExecutions": completed_executions,
        # Field aliases for maximum compatibility
        "usersCount": total_users,
        "runbooksCount": total_runbooks,
        "activeRunbooksCount": active_runbooks,
        "inactiveRunbooksCount": inactive_runbooks,
        "activeExecutions": running_executions,
        "finishedExecutions": completed_executions,
    }
