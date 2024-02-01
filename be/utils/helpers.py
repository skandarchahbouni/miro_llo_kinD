def get_changes(old: dict | None, new: dict | None) -> tuple[list, list, list]:
    """
    This function compares between the old and new dict and returns the changes detected, which could be:
        - New components added to the application.
        - Some components Deleted from the application.
        - Some components changed the cluster (migration).
    """
    # All the components were added
    if old is None:
        return new, [], []

    # All the components were removed
    if new is None:
        return [], old, []

    added_components = [obj for obj in new if obj not in old]
    removed_components = [obj for obj in old if obj not in new]

    old_dict = {obj["name"]: obj["cluster"] for obj in old}
    new_dict = {obj["name"]: obj["cluster"] for obj in new}

    migrated_components = [
        {"name": name, "old_cluster": old_dict[name], "new_cluster": new_dict[name]}
        for name in set(old_dict) & set(new_dict)
        if old_dict[name] != new_dict[name]
    ]

    return added_components, removed_components, migrated_components
