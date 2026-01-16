"""
Time rounding service for applying configurable rounding rules to durations.

Provides consistent rounding logic used when stopping timers and saving manual entries.
"""
from datetime import timedelta
from typing import Literal


class TimeRounding:
    """
    Service class for applying time rounding rules to durations.

    Supports configurable rounding intervals (5, 10, 15, 30 minutes) and
    methods (up, down, nearest) based on user preferences.
    """

    VALID_INTERVALS = [0, 5, 10, 15, 30]
    VALID_METHODS = ['up', 'down', 'nearest']

    @classmethod
    def round_duration(
        cls,
        duration: timedelta,
        interval_minutes: int,
        method: Literal['up', 'down', 'nearest'] = 'nearest'
    ) -> timedelta:
        """
        Apply time rounding to a duration.

        Args:
            duration: Duration to round
            interval_minutes: Rounding interval in minutes (5, 10, 15, 30, or 0 for no rounding)
            method: Rounding method ('up', 'down', or 'nearest')

        Returns:
            timedelta: Rounded duration

        Raises:
            ValueError: If interval or method is invalid
        """
        if interval_minutes not in cls.VALID_INTERVALS:
            raise ValueError(
                f"Invalid interval: {interval_minutes}. "
                f"Must be one of {cls.VALID_INTERVALS}"
            )

        if method not in cls.VALID_METHODS:
            raise ValueError(
                f"Invalid method: {method}. "
                f"Must be one of {cls.VALID_METHODS}"
            )

        # No rounding if interval is 0
        if interval_minutes == 0 or not duration:
            return duration

        # Convert duration to total minutes
        total_minutes = duration.total_seconds() / 60

        # Apply rounding based on method
        if method == 'up':
            # Always round up to next interval
            rounded_minutes = int(((total_minutes + interval_minutes - 1) // interval_minutes) * interval_minutes)
        elif method == 'down':
            # Always round down to previous interval
            rounded_minutes = int((total_minutes // interval_minutes) * interval_minutes)
        else:  # nearest
            # Round to nearest interval
            rounded_minutes = int(round(total_minutes / interval_minutes) * interval_minutes)

        # Ensure we don't round to 0 or negative when rounding down
        if rounded_minutes <= 0:
            rounded_minutes = interval_minutes

        return timedelta(minutes=rounded_minutes)

    @classmethod
    def get_rounding_info(
        cls,
        duration: timedelta,
        interval_minutes: int,
        method: str
    ) -> dict:
        """
        Get both actual and rounded duration for display/confirmation.

        Args:
            duration: Original duration
            interval_minutes: Rounding interval in minutes
            method: Rounding method

        Returns:
            dict: Contains 'actual', 'rounded', and 'difference' durations
        """
        if interval_minutes == 0:
            return {
                'actual': duration,
                'rounded': duration,
                'difference': timedelta(0),
                'applied': False,
            }

        rounded = cls.round_duration(duration, interval_minutes, method)
        difference = rounded - duration

        return {
            'actual': duration,
            'rounded': rounded,
            'difference': difference,
            'applied': True,
        }
