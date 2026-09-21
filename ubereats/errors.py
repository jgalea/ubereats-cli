class UberEatsError(Exception):
    exit_code = 1


class ChallengeError(UberEatsError):
    exit_code = 4


class AuthError(UberEatsError):
    exit_code = 5


class LocationError(UberEatsError):
    exit_code = 6


class NotFoundError(UberEatsError):
    exit_code = 7


class ApiError(UberEatsError):
    exit_code = 8
