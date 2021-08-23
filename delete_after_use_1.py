class CustomPy3CompatibleJobStore(SQLAlchemyJobStore):
    def get_due_jobs(self, now):
        jobs = []
        try:
            jobs = super().get_due_jobs(now)
        except RuntimeError as e:
            logger.info("Handled StopIteration from empty generator, returning empty job store list")
        return jobs


def start_scheduler():
    global _scheduler
    _scheduler = TornadoScheduler(gconfig={'misfire_grace_time': 10})
    sql_alchemy_engine = get_engine()
    if not sql_alchemy_engine:
        logger.error('AP Scheduler could not be started. SQLAlchemy engine not yet initialized.')
        return
    _scheduler.add_jobstore(CustomPy3CompatibleJobStore(engine=get_engine()), 'TriggersShelveStore')

    if not _scheduler.running:
        _scheduler.start()
        _scheduler.add_listener(log_execution_job_status, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    if task_config.ENV not in ['prod']:
        _scheduler.add_listener(add_job_event, EVENT_JOB_ADDED | EVENT_JOB_REMOVED)
    logger.info('Started AP Scheduler. Using SQLAlchemyJobStore.\n')
    return _scheduler
