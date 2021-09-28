class ImplementationError(Exception):
    """A general error for poor implementation. Usually used in subclasses."""
    pass


class ConfigurationError(Exception):
    """The user has configured something incorrectly."""
    pass


class CommandError(Exception):
    """An incorrect command passed to the motor."""
    pass
