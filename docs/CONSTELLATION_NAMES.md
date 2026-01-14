# Constellation Name Generator Documentation

The Constellation Name Generator is a utility that provides unique, astronomy-themed default names for personal workspaces when users don't specify a custom workspace name during registration.

## Overview

When a user registers without providing a workspace name, the system automatically assigns a random constellation name to their personal workspace. This adds a delightful, personal touch while maintaining a professional aesthetic.

## Location

The constellation name generator is located in:
```
accounts/utils.py
```

## Implementation

### Class: `ConstellationNameGenerator`

The generator is implemented as a class with class methods for generating constellation names.

#### Available Constellation Names

The system includes the following pre-defined constellation names:

1. Orion
2. Andromeda
3. Cassiopeia
4. Lyra
5. Cygnus
6. Perseus
7. Draco
8. Ursa Major
9. Phoenix
10. Centaurus

### Methods

#### `generate()`

Generates a random constellation name from the predefined list.

**Usage:**
```python
from accounts.utils import ConstellationNameGenerator

name = ConstellationNameGenerator.generate()
# Returns: "Orion", "Andromeda", etc. (random selection)
```

**Returns:**
- `str`: A randomly selected constellation name

**Example:**
```python
>>> ConstellationNameGenerator.generate()
'Cassiopeia'
>>> ConstellationNameGenerator.generate()
'Draco'
```

#### `generate_unique(existing_names=None)`

Generates a unique constellation name, adding a numeric suffix if all base names are already taken.

**Parameters:**
- `existing_names` (list, optional): List of existing workspace names to avoid duplicates

**Returns:**
- `str`: A unique constellation name, potentially with numeric suffix

**Logic:**
1. First attempts to select an unused constellation name from the base list
2. If all base names are taken, adds a numeric suffix (e.g., "Orion 2", "Andromeda 3")
3. Increments the suffix until a unique name is found

**Example:**
```python
# No existing names - returns a random constellation
>>> ConstellationNameGenerator.generate_unique([])
'Phoenix'

# Some names exist - returns unused constellation
>>> ConstellationNameGenerator.generate_unique(['Orion', 'Lyra'])
'Cassiopeia'  # One of the unused names

# All base names exist - returns name with numeric suffix
>>> all_names = ['Orion', 'Andromeda', 'Cassiopeia', 'Lyra', 'Cygnus',
...              'Perseus', 'Draco', 'Ursa Major', 'Phoenix', 'Centaurus']
>>> ConstellationNameGenerator.generate_unique(all_names)
'Orion 1'  # Adds numeric suffix

# Some names with suffixes exist
>>> existing = ['Orion', 'Orion 1', 'Orion 2', 'Andromeda']
>>> ConstellationNameGenerator.generate_unique(existing)
'Orion 3'  # Next available suffix
```

### Utility Function: `generate_constellation_name(user=None)`

A convenience function that wraps the generator with user-specific logic.

**Parameters:**
- `user` (optional): User object to check for existing workspace names

**Returns:**
- `str`: A unique constellation name for the workspace

**Logic:**
1. If a user is provided, queries their existing workspace names
2. Calls `generate_unique()` with the existing names to ensure uniqueness
3. If no user is provided, calls `generate()` for a random name

**Usage:**
```python
from accounts.utils import generate_constellation_name

# Without user (random name)
name = generate_constellation_name()

# With user (ensures uniqueness across user's workspaces)
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='user@example.com')
name = generate_constellation_name(user=user)
```

## How to Add or Modify Constellation Names

### Adding New Constellation Names

To add new constellation names to the system:

1. Open `accounts/utils.py`
2. Locate the `ConstellationNameGenerator` class
3. Find the `CONSTELLATION_NAMES` list
4. Add new constellation names to the list:

```python
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
    'Centaurus',
    # Add new names below
    'Aquila',
    'Gemini',
    'Scorpius',
]
```

### Removing Constellation Names

To remove a constellation name:

1. Open `accounts/utils.py`
2. Remove the name from the `CONSTELLATION_NAMES` list
3. Note: Existing workspaces with that name will not be affected

### Best Practices for Constellation Names

When adding new constellation names, consider:

1. **Length**: Keep names reasonably short (1-3 words)
2. **Spelling**: Use standard astronomical spellings
3. **Cultural Sensitivity**: Choose well-known, internationally recognized constellations
4. **Pronunciation**: Select names that are easy to pronounce in English
5. **Variety**: Mix short and longer names for visual diversity

### Recommended Constellation Names to Add

If you want to expand the list, consider these additional constellations:

- Aquila (Eagle)
- Gemini (Twins)
- Leo (Lion)
- Scorpius (Scorpion)
- Taurus (Bull)
- Virgo (Virgin)
- Pegasus (Winged Horse)
- Hercules (Hero)
- Hydra (Water Snake)
- Polaris (North Star)

## Duplicate Handling Strategy

The system handles duplicate workspace names through the following strategy:

### For Different Users

Users can have workspaces with the same name as other users' workspaces. The system only ensures uniqueness within a single user's workspace collection.

Example:
- User A can have a workspace named "Orion"
- User B can also have a workspace named "Orion"
- This is allowed because they are different users

### For Same User

A single user cannot have multiple workspaces with the exact same name. The system enforces this through:

1. **Database Constraint**: Unique constraint on (owner, name) in the Workspace model
2. **Application Logic**: `generate_unique()` method checks existing names
3. **Numeric Suffix**: Adds numbers when base names are exhausted

Example:
- User creates first workspace: "Orion"
- User creates second workspace: "Orion 1" (automatic)
- User creates third workspace: "Orion 2" (automatic)

### Suffix Format

When adding numeric suffixes:
- Format: `<constellation_name> <number>`
- Starting number: 1
- Increment: 1
- Examples: "Orion 1", "Andromeda 2", "Cassiopeia 10"

## Integration with Workspace Creation

The constellation name generator is integrated into the workspace creation flow through Django signals.

### Automatic Usage During Registration

When a user registers:

1. **With Custom Workspace Name**: User-provided name is used directly
2. **Without Workspace Name**: `generate_constellation_name(user)` is called to assign a random constellation

**Implementation:**
```python
# In accounts/signals.py (or similar)
from .utils import generate_constellation_name

def create_user_workspace(sender, instance, created, **kwargs):
    if created:
        workspace_name = instance.workspace_name or generate_constellation_name(instance)
        Workspace.objects.create(
            owner=instance,
            name=workspace_name,
            is_personal=True
        )
```

## Testing

The constellation name generator includes tests to verify:

1. `generate()` returns a name from the predefined list
2. `generate_unique()` returns unused names when available
3. `generate_unique()` adds numeric suffix when all base names are used
4. Numeric suffix increments correctly for duplicates
5. User-specific uniqueness checks work correctly

**Test Location:**
```
accounts/tests/test_models_workspace.py
```

## Customization Ideas

### Theme-Based Names

Instead of constellations, you could use:
- Greek gods: Zeus, Athena, Apollo
- Planets: Mercury, Venus, Mars
- Elements: Carbon, Oxygen, Nitrogen
- Colors: Crimson, Azure, Emerald

To implement a theme change, simply replace the `CONSTELLATION_NAMES` list with your preferred theme.

### Dynamic Name Generation

For more advanced use cases, you could:
- Load names from a database table
- Allow admins to manage names through Django admin
- Fetch names from an API
- Generate procedural names (adjective + noun combinations)

## Performance Considerations

The constellation name generator is highly efficient:

- **Memory**: Stores only 10 names in memory (minimal footprint)
- **Time Complexity**: O(n) for `generate_unique()` where n = number of existing names
- **Database Queries**: 1 query to fetch existing workspace names (when user provided)

For large-scale deployments with thousands of users, the performance remains excellent as:
- Each user only has a few workspaces
- Uniqueness check is scoped to single user
- Database query uses indexed foreign key (owner)

## Conclusion

The Constellation Name Generator provides a simple, delightful way to assign default workspace names while maintaining uniqueness and extensibility. The astronomy theme aligns with Workstate's philosophy of bringing clarity and structure to work tracking.
