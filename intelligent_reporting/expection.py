class ReportingException(Exception):
    pass

class FileConnectorNotFound(ReportingException):
    pass

class DBConnectorNotRegistered(ReportingException):
    pass

# Data errors
class DataLoadingError(ReportingException):
    pass

class EmptyDatasetError(ReportingException):
    pass

# Configuration / usage
class ConfigurationError(ReportingException):
    pass

class SchemaInfererNotRegistered(ReportingException):
    pass


class MissingDialectOrDriverError(ReportingException):
    pass


class AuthenticationError(ReportingException):
    pass


class NetworkError(ReportingException):
    pass


class DatabaseNotFoundError(ReportingException):
    pass


class PermissionError(ReportingException):
    pass


class UnknownDatabaseError(ReportingException):
    pass
