class Base(object):
    """DB driver is injected in the init method."""

    def __init__(self):
        super().__init__()

        # self.db = cinder.db
        # self.db.dispose_engine()
        self.db=None
