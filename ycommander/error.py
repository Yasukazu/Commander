#  _  __  
# | |/ /___ ___ _ __  ___ _ _ ®
# | ' </ -_) -_) '_ \/ -_) '_|
# |_|\_\___\___| .__/\___|_|
#              |_|            
#
# Keeper Commander 
# Contact: ops@keepersecurity.com
#

class Error(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, message):
        self.message = message


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class AuthenticationError(Error):
    """Exception raised with user fails authentication

    Attributes:
        message -- explanation of authentication error
    """

    def __init__(self, message):
        self.message = message

class CommunicationError(Error):
    """Exception raised with network issues

    Attributes:
        message -- explanation of communication error
    """

    def __init__(self, message):
        self.message = message


class KeeperApiError(CommunicationError):
    """Exception raised with failed Keeper API request
    """

    def __init__(self, result_code, message):
        CommunicationError.__init__(self, message)
        self.result_code = result_code

    def __str__(self):
        return self.message or self.result_code


class NoUserExistsError(KeeperApiError):
    pass


class CryptoError(Error):
    """Exception raised with cryptography issues

    Attributes:
        message -- explanation of crypto error
    """

    def __init__(self, message):
        self.message = message

class OSException(Error):
    """OS or I/O error
    """
    def __init__(self, message):
        self.message = message

class NonSupportedType(Error):
    """not supported type error
    """
    def __init__(self, message):
        self.message = message

class TimestampError(Error):
    """failed to get timestamp
    """
    def __init__(self, message):
        self.message = message

class RecordError(Error):
    """Fail in getting data in a record
    """
    pass

class ExecutuonError(Error):
    """Fail in executing a command
    """
    pass


class ArgumentError(Error, ValueError):
    pass


class ParseError(Error):
    """Fail in parsing command parameters
    """
    pass

class DecodeError(Error):
    """Fail in decoding data
    """
    pass

class SequenceError(Error):
    """Bad call sequence
    """
    pass

class DataError(Error):
    """Bad data
    """
    pass

class EmptyError(DataError):
    """data is empty
    """
    pass

class ResolveError(Error):
    """Failed to resolve data
    """
    pass

class ConfigError(Error):
    '''Failed to config
    '''
    pass

class QuitException(Error):
    """Exception to quit Shell
    """
    pass

