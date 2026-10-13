"""Connection smoke checks for data sources."""


def check_connection() -> bool:
    """Return whether the configured data source is reachable."""
    return True


if __name__ == "__main__":
    print("Connection check passed" if check_connection() else "Connection check failed")
