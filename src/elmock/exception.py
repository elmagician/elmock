class UnexpectedMethod(Exception):
    def __init__(self, method: str = "undefined"):
        self.message = f'Method {method} was not expected'


class UnexpectedArguments(Exception):
    def __init__(self, method: str = "undefined", *args, **kwargs):
        self.message = f'Method {method} did not expected to be called with {args}, {kwargs}'


class UnexpectedCall(Exception):
    def __init__(self, method: str, *args, **kwargs):
        self.message = f'Call to method {method} with arguments {args}, {kwargs} was not expected'


class NotFullFilled(Exception):
    def __init__(self, data):
        self.message = 'Some calls where not full filled:\n'
        for d in data:
            self.message += f'- {d.method} ' \
                            f'  arg: {d.args}' \
                            f'  kwargs: {d.kwargs}' \
                            f'  was expected to happen {d.expected} ' \
                            f'  but was called {d.called}'
