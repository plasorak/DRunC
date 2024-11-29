from drunc.exceptions import DruncSetupException, DruncCommandException, DruncException

class UnknownProcessManagerType(DruncSetupException):
    def __init__(self, pm_type):
        super().__init__(f'\'{pm_type}\' is not handled/unknown')

class BadQuery(DruncCommandException):
    pass

class DruncK8sNamespaceAlreadyExists(DruncException): # Exceptions that gets thrown when namespaces already exists
    pass

class EnvironmentVariableCannotBeSet(DruncException):
    pass
