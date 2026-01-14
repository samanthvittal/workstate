"""
Utility functions for the accounts app.
"""
import random


class ConstellationNameGenerator:
    """
    Generator for random constellation names to be used as default workspace names.
    """

    # Pre-defined list of constellation names
    CONSTELLATION_NAMES = [
        'Orion',
        'Andromeda',
        'Cassiopeia',
        'Lyra',
        'Cygnus',
        'Perseus',
        'Draco',
        'Ursa Major',
        'Phoenix',
        'Centaurus'
    ]

    @classmethod
    def generate(cls):
        """
        Generate a random constellation name.

        Returns:
            str: A randomly selected constellation name from the predefined list.
        """
        return random.choice(cls.CONSTELLATION_NAMES)

    @classmethod
    def generate_unique(cls, existing_names=None):
        """
        Generate a unique constellation name, adding numeric suffix if needed.

        Args:
            existing_names (list, optional): List of existing workspace names to avoid.

        Returns:
            str: A unique constellation name, with numeric suffix if needed.
        """
        if existing_names is None:
            existing_names = []

        # Convert to set for faster lookup
        existing_names_set = set(existing_names)

        # Try base constellation names first
        available_names = [name for name in cls.CONSTELLATION_NAMES
                          if name not in existing_names_set]

        if available_names:
            return random.choice(available_names)

        # If all base names are taken, add numeric suffix
        base_name = random.choice(cls.CONSTELLATION_NAMES)
        counter = 1

        while f"{base_name} {counter}" in existing_names_set:
            counter += 1

        return f"{base_name} {counter}"


def generate_constellation_name(user=None):
    """
    Utility function to generate a constellation name for workspace creation.

    Args:
        user: Optional user object to check their existing workspace names.

    Returns:
        str: A unique constellation name for the workspace.
    """
    if user:
        # Get existing workspace names for this user
        from .models import Workspace
        existing_names = list(
            Workspace.objects.filter(owner=user).values_list('name', flat=True)
        )
        return ConstellationNameGenerator.generate_unique(existing_names)
    else:
        return ConstellationNameGenerator.generate()
