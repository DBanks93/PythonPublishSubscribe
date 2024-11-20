class PythonPublishSubscribe:
    def __init__(self, config=None):
        self.config = config or {}
        self.initialise()

    def initialise(self):
        print("initialise")

    def run(self):
        print("run")