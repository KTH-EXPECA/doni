from oslo_config import cfg

GROUP = "worker"

opts = [
    cfg.IntOpt(
        "task_pool_size",
        min=1,
        default=1000,
        help=(
            "The number of greenthreads to use for periodic task execution. "
            "The higher this number, the more worker tasks and other "
            "background async jobs can be effectively executed in parallel. "
            "See ``task_concurrency`` if you would like to limit how many "
            "worker tasks specifically are allowed to execute; in general it "
            "it best to leave this at its default. Defaults to 1000."
        ),
    ),
    cfg.IntOpt(
        "process_pending_task_interval",
        min=1,
        default=60,
        help=(
            "How often to invoke the process_pending periodic task, "
            "which handles and executes pending worker tasks. The "
            "lower this value, the faster worker tasks will be "
            "processed on average, but at the cost of a greater "
            "amount of database calls as part of task overhead."
        ),
    ),
    cfg.IntOpt(
        "task_concurrency",
        min=1,
        default=1000,
        help=(
            "The number of worker tasks that can execute in parallel. "
            "This will be bounded by ``task_pool_size``, so reasonable values "
            "should be less than or equal to that setting. This setting can "
            "introduce artificial constraints on worker task execution, while "
            "still allowing other async operations such as worker periodic "
            "tasks to run as normal."
        ),
    ),
]
