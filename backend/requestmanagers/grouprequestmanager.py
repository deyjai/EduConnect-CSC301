from flask import request
from requestmanagers.requestmanager import RequestManager
from databasemanager import DatabaseManager


class GroupRequestManager(RequestManager):
    def __init__(self):
        RequestManager.__init__(self)

    def get_group(self, id):
        """
        Get a group.
        :param id: The id of the group
        :return: If the operation was successful or not
        """
        group = DatabaseManager.instance().get_group(id)
        if group is None:
            return self._respond(status_code=404)

        owner = DatabaseManager.instance().get_user(group.get_owner())
        if owner is None:
            return self._respond(status_code=404)

        enrolled = DatabaseManager.instance().get_group_enrolled(id)
        res = {
            "id": group.get_id(),
            "title": group.get_name(),
            "description": group.get_description(),
            "instructor": owner.get_email(),
            "enrolled": enrolled,
            "banner": "https://picsum.photos/1920/1080"
        }

        return self._respond(status_code=200, body=res)

    def post_create_group(self):
        """
        Handle a POST request for creating a new educational group.
        :return: The details of the created group
        """
        data = request.get_json()
        user_id = data.get("userid")
        owner = DatabaseManager.instance().get_user(user_id)

        if owner is None:
            body = {
                "message": "Owner not found. Please provide a valid owner ID."
            }
            return self._respond(status_code=404, body=body)

        group_name = data.get("groupName")
        group_desc = data.get("groupDesc")

        if len(group_name) <= 0 or len(group_desc) <= 0:
            body = {
                "message": "Please provide a valid title and description."
            }
            return self._respond(status_code=401, body=body)

        new_group = DatabaseManager.instance().create_group(group_name, group_desc, user_id)

        if new_group is not None:
            return self._respond(status_code=200)

        body = {
            "message": "Failed to create the group. Please try again."
        }
        return self._respond(status_code=500, body=body)

    def post_join_group(self, id):
        """
        Join a group.
        :param id: The id of the group
        :return: Whether the join was successful or not
        """
        data = request.get_json()
        joined = DatabaseManager.instance().join_group(data["userid"], id)

        if not joined:
            return self._respond(status_code=202)

        return self._respond(status_code=200)

    def get_all_groups(self):
        """
        Get all groups in the database.
        :return: All groups in the database
        """
        groups = DatabaseManager.instance().get_all_groups()
        res = []
        for group in groups:
            enrolled = DatabaseManager.instance().get_group_enrolled(group.get_id())
            g = {
                "id": group.get_id(),
                "title": group.get_name(),
                "description": group.get_description(),
                "owner": group.get_owner(),
                "enrolled": enrolled
            }

            res.append(g)

        return self._respond(status_code=200, body=res)

    def get_user_groups(self, id):
        """
        Handle a GET request for a list of educational groups owned by a user.
        :return: List of educational groups
        """
        user = DatabaseManager.instance().get_user(id)

        if user is None:
            return self._respond(status_code=404)

        groups = DatabaseManager.instance().get_groups_by_user(id)

        res = []
        for group in groups:
            enrolled = DatabaseManager.instance().get_group_enrolled(group.get_id())
            g = {
                "id": group.get_id(),
                "title": group.get_name(),
                "description": group.get_description(),
                "owner": group.get_owner(),
                "enrolled": enrolled
            }

            res.append(g)

        return self._respond(status_code=200, body=res)