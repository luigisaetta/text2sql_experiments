"""
Profile Manager

To handle user related information:
    user_group_id: the id of the group the user belongs to
"""


class ProfileManager:
    """
    The class handle all the profile of the user
    """

    def __init__(self, user_name=None, user_group_id=None):
        self.user_name = user_name
        self.user_group_id = user_group_id

    def get_user_group_id(self):
        """
        return the user_group_id used in RBAC
        """
        return self.user_group_id
