"""Password rules shared by sign-up, password change, admin reset and the CLI."""

MIN_PASSWORD_LENGTH = 8

# Very common passwords that meet the length rule. Lower-cased.
COMMON_PASSWORDS = frozenset(
    {
        "password",
        "password1",
        "password12",
        "password123",
        "password1234",
        "passw0rd",
        "p@ssw0rd",
        "p@ssword",
        "12345678",
        "123456789",
        "1234567890",
        "123123123",
        "11111111",
        "00000000",
        "87654321",
        "qwertyui",
        "qwerty12",
        "qwerty123",
        "qwertyuiop",
        "1q2w3e4r",
        "1qaz2wsx",
        "zaq12wsx",
        "abcd1234",
        "abc12345",
        "iloveyou",
        "sunshine",
        "princess",
        "football",
        "baseball",
        "superman",
        "trustno1",
        "letmein1",
        "welcome1",
        "welcome123",
        "admin123",
        "administrator",
        "changeme",
        "changeme123",
        "monkey123",
        "dragon123",
    }
)


def password_problem(password: str) -> str | None:
    """Return why a password is not acceptable, or None if it is fine."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if password.lower() in COMMON_PASSWORDS:
        return "This password is too common; choose another"
    return None
