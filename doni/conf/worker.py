from oslo_config import cfg

GROUP = "worker"

opts = [
    cfg.IntOpt("task_pool_size", min=1, default=1000,
               help=("The number of greenthreads to use for worker execution. "
                     "The higher this number, the more worker tasks can be "
                     "effectively executed in parallel. Defaults to 1000.")),
    cfg.IntOpt("process_pending_task_interval", min=1, default=60,
               help=("How often to invoke the process_pending periodic task, "
                     "which handles and executes pending worker tasks. The "
                     "lower this value, the faster worker tasks will be "
                     "processed on average, but at the cost of a greater "
                     "amount of database calls as part of task overhead.")),
]
