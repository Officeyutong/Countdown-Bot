class InvalidAccessTokenException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class APIError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
