from rbq.settings import *

ALLOWED_HOSTS = ["rbq.localdomain"]

RBQ_LOCAL_DOMAINS = ["rbq.localdomain"]

Q_CLUSTER["save_limit"] = -1
Q_CLUSTER["sync"] = True