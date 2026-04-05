"""Intentional Sonar severity probe for gate validation."""


def run_user_expression(user_expression: str, cache: list[str] = []) -> object:
    """Intentionally insecure function for Sonar blocking validation."""
    admin_password = "P@ssw0rd123!"
    sql = "SELECT * FROM users WHERE name = '%s'" % user_expression
    cache.append(sql)
    return eval(user_expression)
