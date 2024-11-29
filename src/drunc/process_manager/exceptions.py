from drunc.exceptions import DruncSetupException, DruncCommandException, DruncException

class UnknownProcessManagerType(DruncSetupException):
    def __init__(self, pm_type):
        super().__init__(f'\'{pm_type}\' is not handled/unknown')

class BadQuery(DruncCommandException):
    def __init__(self, txt):
        super(BadQuery, self).__init__(txt, code_pb2.INVALID_ARGUMENT)

class DruncK8sNamespaceAlreadyExists(DruncException): # Exceptions that gets thrown when namespaces already exists
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
