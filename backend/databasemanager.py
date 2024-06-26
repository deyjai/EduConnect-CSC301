from user import User
import psycopg2 as pg
from event import Event
from group import Group
from announcement import Announcement
from comment import AnnouncementComment


class DatabaseManager(object):
    """
    A singleton database manager. Access it using instance().
    """
    _instance = None
    connection = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()

        return cls._instance

    def _initialize(self):
        try:
            self.connection = pg.connect("user=postgres password=admin")
            self._setup_database()
            return True
        except pg.Error as ex:
            print(ex)
            return False

    def _clear_database(self):
        """
        WARNING: This will clear the entire database. Use for testing purposes only.
        """
        with self.connection.cursor() as curs:
            curs.execute("DROP SCHEMA IF EXISTS edu_connect CASCADE;")
            self.connection.commit()

    def _setup_database(self):
        # self._clear_database()
        cursor, schema_file = None, None

        try:
            cursor = self.connection.cursor()

            schema_file = open("schema.ddl", "r")
            cursor.execute(schema_file.read())

            self.connection.commit()
        except Exception as ex:
            self.connection.rollback()
            raise Exception(f"Could not setup the schema: \n{ex}")
        finally:
            if cursor and not cursor.closed:
                cursor.close()
            if schema_file:
                schema_file.close()

    def register_user(self, email: str, username: str, password: str) -> User | None:
        """
        Register a new user into the database.
        :param password: The user's password
        :param username: The user's username
        :param email: The user's email
        :return: The User object if the registration was successful, None otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO edu_user(username, email, password) VALUES(%s, %s, %s) RETURNING id;",
                           [username, email, password])

            new_id = cursor.fetchone()
            if new_id[0] <= 0:
                return None

            self.connection.commit()
            print("Created user with ID: " + str(new_id[0]))
            return User(new_id[0], email, username, password)
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def login_user(self, email: str, password: str) -> User | None:
        """
        Attempt to retrieve a user with the given email and password, and return it if it exists.
        :param email: The user's email
        :param password: The user's password
        :return: The User if they exist, None otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM edu_user WHERE email = %s AND password = %s", [email, password])
            if cursor.rowcount <= 0:
                return None

            r = cursor.fetchone()
            user = User(int(r[0]), r[2], r[1], r[3])
            self.connection.commit()
            return user
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def update_user_email(self, user_id: int, email: str) -> bool:
        """
        Update a user's email.
        :param user_id: The user's ID
        :param email: The new email
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE edu_user SET email = %s WHERE id = %s", [email, user_id])
            self.connection.commit()
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def update_user_username(self, user_id: int, username: str) -> bool:
        """
        Update a user's email.
        :param user_id: The user's ID
        :param username: The new username
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE edu_user SET username = %s WHERE id = %s", [username, user_id])
            self.connection.commit()
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def update_user_password(self, user_id: int, password: str) -> bool:
        """
        Update a user's email.
        :param user_id: The user's ID
        :param password: The new password
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE edu_user SET password = %s WHERE id = %s", [password, user_id])
            self.connection.commit()
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_user(self, identifier: int) -> User | None:
        """
        Get a user with the given identifier.
        :param identifier: The identifier of the user
        :return: Object for the user, or None if not found
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM edu_user WHERE id = %s", [identifier])
            if cursor.rowcount <= 0:
                return None

            r = cursor.fetchone()
            user = User(int(r[0]), r[2], r[1], r[3])
            self.connection.commit()
            return user
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_group_messages(self, group_id: int) -> list:
        """
        Get all the messages in the given group.
        :param group_id: The ID of the group
        :return: A list of messages
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM group_chat WHERE group_id = %s", [group_id])
            if cursor.rowcount <= 0:
                return []

            messages = []
            for record in cursor:
                user = self.get_user(record[2])

                if user is not None:
                    msg = {
                        "sender": record[2],
                        "sender_name": user.get_username(),
                        "content": record[1],
                        "date": str(record[4])
                    }
                    messages.append(msg)

            self.connection.commit()
            return messages
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_announcements(self, group_id: int) -> list:
        """
        Get all the announcements in the given group.
        :param group_id: The group to look for announcements in
        :return: A list of all the announcements in the group
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM announcement WHERE group_id = %s", [group_id])
            if cursor.rowcount <= 0:
                return []

            announcements = []
            for record in cursor:
                upvotes = self.get_announcement_upvotes(record[0])
                downvotes = self.get_announcement_downvotes(record[0])
                ann = Announcement(record[0], record[1], record[2], record[4], record[3], upvotes, downvotes)
                announcements.append(ann)

            self.connection.commit()
            return announcements
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_announcement(self, identifier: int) -> Announcement | None:
        """
        Get an announcement with the given identifier.
        :param identifier: The identifier of the announcement
        :return: Object for the announcement, or None if not found
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM announcement WHERE id = %s", [identifier])
            if cursor.rowcount <= 0:
                return None

            r = cursor.fetchone()
            upvotes = self.get_announcement_upvotes(identifier)
            downvotes = self.get_announcement_downvotes(identifier)
            announcement = Announcement(identifier, r[1], r[2], r[4], r[3], upvotes, downvotes)
            self.connection.commit()
            return announcement
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_announcement_upvotes(self, identifier: int) -> int:
        """
        Get an announcement upvote count with the given identifier.
        :param identifier: The identifier of the announcement
        :return: The number of votes
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT count(*) FROM announcement_upvotes WHERE announcement = %s", [identifier])
            r = cursor.fetchone()
            self.connection.commit()
            return r[0]
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return 0
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_announcement_downvotes(self, identifier: int) -> int:
        """
        Get an announcement downvote count with the given identifier.
        :param identifier: The identifier of the announcement
        :return: The number of votes
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT count(*) FROM announcement_downvotes WHERE announcement = %s", [identifier])
            r = cursor.fetchone()
            self.connection.commit()
            return r[0]
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return 0
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def post_announcement(self, group: int, poster: int, message: str):
        """
        Post a new announcement to the given group.
        :param group: The group to post the announcement to
        :param poster: The person posting the announcement
        :param message: The message in the announcement
        :return: The object for the announcement
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO announcement(poster_id, group_id, message) VALUES (%s, %s, %s) "
                           "RETURNING id, date;", [poster, group, message])

            res = cursor.fetchone()
            new_id = res[0]
            new_date = res[1]

            if new_id <= 0:
                return None

            self.connection.commit()

            new_announcement = Announcement(new_id, poster, group, str(new_date), message, 0, 0)
            return new_announcement
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def upvote_announcement(self, announcement: int, user_id: int) -> bool:
        """
        Upvote an announcement.
        :param announcement: The ID of the announcement
        :param user_id: The ID of the user making the vote
        :return: If the upvote was added
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM announcement_upvotes WHERE announcement = %s AND voter = %s",
                           [announcement, user_id])

            # Remove the upvote if it exists already
            if cursor.rowcount > 0:
                self.connection.commit()
                cursor.execute("DELETE FROM announcement_upvotes WHERE announcement = %s AND voter = %s",
                               [announcement, user_id])
                self.connection.commit()
                return False

            cursor.execute("INSERT INTO announcement_upvotes(announcement, voter) VALUES (%s, %s)",
                           [announcement, user_id])
            self.connection.commit()
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def downvote_announcement(self, announcement: int, user_id: int) -> bool:
        """
        Downvote an announcement.
        :param announcement: The ID of the announcement
        :param user_id: The ID of the user making the vote
        :return: If the downvote was added
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM announcement_downvotes WHERE announcement = %s AND voter = %s",
                           [announcement, user_id])

            # Remove the downvote if it exists already
            if cursor.rowcount > 0:
                self.connection.commit()
                cursor.execute("DELETE FROM announcement_downvotes WHERE announcement = %s AND voter = %s",
                               [announcement, user_id])
                self.connection.commit()
                return False

            cursor.execute("INSERT INTO announcement_downvotes(announcement, voter) VALUES (%s, %s)",
                           [announcement, user_id])
            self.connection.commit()
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def create_group(self, name: str, desc: str, owner: int) -> Group | None:
        """
        Create a new educational group in the database.
        :param name: The name of the group
        :param desc: The description of the group
        :param owner: The owner of the group
        :return: The Group object if the creation was successful, None otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO edu_group(name, description, owner) VALUES (%s, %s, %s) RETURNING id, creation_date;",
                           [name, desc, owner])

            new_id = cursor.fetchone()
            if new_id[0] <= 0:
                return None

            self.connection.commit()
            print("Created group with ID: " + str(new_id[0]))
            return Group(new_id[0], name, desc, owner, new_id[1])
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_group(self, group_id: int) -> Group | None:
        """
        Get an educational group with the given identifier.
        :param group_id: The identifier of the group to find
        :return: Group object, or None if not found
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM edu_group WHERE id = %s", [group_id])
            if cursor.rowcount <= 0:
                return None

            g = cursor.fetchone()
            group = Group(g[0], g[1], g[2], g[3], g[4])
            self.connection.commit()
            return group
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_all_groups(self, exclude_user: int = -1) -> list[Group]:
        """
        Get all groups.
        :return: A list of all groups.
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM edu_group")

            groups = []
            for record in cursor:
                group = Group(record[0], record[1], record[2], record[3], record[4])
                groups.append(group)

            self.connection.commit()
            return groups
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_groups_by_user(self, user_id: int) -> list[Group]:
        """
        Get a list of educational groups a user is a part of.
        :param user_id: The identifier of the user
        :return: List of Group objects
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM group_member WHERE member_id = %s", [user_id])

            groups = []
            for record in cursor:
                group = self.get_group(record[0])
                if group is not None:
                    groups.append(group)

            self.connection.commit()
            return groups
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_group_enrolled(self, group_id: int) -> int:
        """
        Get the number of students enrolled in a group.
        :param group_id: The ID of the group
        :return: The number of students enrolled
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM group_member WHERE group_id = %s", [group_id])
            res = cursor.fetchone()[0]
            self.connection.commit()
            return res
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return 0
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def join_group(self, user_id: int, group_id: int) -> bool:
        """
        Join the group with the given user.
        :param user_id: The user joining
        :param group_id: The group to join
        :return: True if the operation was successful, false otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO group_member(group_id, member_id) VALUES (%s, %s)", [group_id, user_id])

            self.connection.commit()
            print(f"User {0} joined group {1}", user_id, group_id)
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def post_event(self, group: Group, poster: User, date: str, title: str, description: str):
        """
        Post a new event to the given group.
        :param group: The group to post the event to
        :param poster: The person posting the event
        :param date: The date of the event
        :param title: The title of the event
        :param description: The description of the event
        :return: The object for the event
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO event(group_id, creator_id, event_date, title, description) "
                           "VALUES (%s, %s, %s, %s, %s) RETURNING id, event_date;",
                           [group.get_id(), poster.get_id(), date, title, description])

            res = cursor.fetchone()
            new_id = res[0]
            new_date = res[1]

            if new_id <= 0:
                return None

            self.connection.commit()

            new_event = Event(new_id, poster.get_id(), group.get_id(), new_date, title, description)
            return new_event
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_group_events(self, group_id: int) -> list[Event]:
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM event WHERE group_id = %s", [group_id])

            events = []
            for record in cursor:
                event = Event(record[0], record[2], record[1], record[3], record[4], record[5])
                events.append(event)

            self.connection.commit()
            return events
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_events(self, user_id: int) -> list[Event]:
        """
        Get all events for a user.
        :return: A list of all events.
        """
        groups = self.get_groups_by_user(user_id)

        events = []
        for group in groups:
            e = self.get_group_events(group.get_id())
            events.extend(e)

        return events

    def join_event(self, user_id: int, event_id: int) -> bool:
        """
        Join the event with the given user.
        :param user_id: The user joining
        :param event_id: The event to join
        :return: True if the operation was successful, false otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO event_attend(event_id, member_id) VALUES (%s, %s)", [event_id, user_id])

            self.connection.commit()
            print(f"User {0} joined group {1}", user_id, event_id)
            return True
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return False
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def get_event_attending(self, event_id: int) -> list[int]:
        """
        Get all the students attending an event.
        :param event_id: The ID of the event
        :return: The list of students attending
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT member_id FROM event_attend WHERE event_id = %s", [event_id])

            ids = []
            for record in cursor:
                ids.append(record[0])

            self.connection.commit()

            return ids
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def insert_chat_personal(self, sender_id: int, receiver_id: int, content: str) -> int:
        """
        Inserts a chat into the specified personal chat
        :param sender_id: The id of the sender of the message
        :param receiver_id: The id of the receiver of the message
        :param content: The contents of the message
        :return: The ID of the new chat, or -1 if it was unsuccessful
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("INSERT INTO personal_chat(content, sender_id, receiver_id) VALUES(%s, %s, %s) RETURNING id",
                           [content, sender_id, receiver_id])

            new_id = cursor.fetchone()
            if new_id[0] < 0:
                return -1

            self.connection.commit()
            print(f"Created chat with ID: {new_id[0]}")
            return new_id[0]
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return -1
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def insert_chat_group(self, sender_id: int, group_id: int, content: str) -> int:
        """
        Inserts a chat into the specified group chat
        :param sender_id: The id of the sender of the message
        :param group_id: The id of the group the message was sent in
        :param content: The contents of the message
        :return: The ID of the new chat, or -1 if it was unsuccessful
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("INSERT INTO group_chat(content, sender_id, group_id) VALUES(%s, %s, %s) RETURNING id",
                           [content, sender_id, group_id])

            new_id = cursor.fetchone()
            if new_id[0] < 0:
                return -1

            self.connection.commit()
            print(f"Created chat with ID: {new_id[0]}")
            return new_id[0]
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return -1
        finally:
            if cursor and not cursor.closed:
                cursor.close()

    def post_comment(self, announcement_id: int, commenter_id: int, comment_text: str) -> AnnouncementComment | None:
        """
        Post a new comment under a certain announcement.
        :param announcement_id: The ID of the announcement
        :param commenter_id: The ID of the user posting the comment
        :param comment_text: The text of the comment
        :return: The object for the comment if the posting was successful, None otherwise
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT INTO announcement_comments(announcement_id, commenter_id, content) "
                           "VALUES (%s, %s, %s) RETURNING id, date",
                           [announcement_id, commenter_id, comment_text])
    
            res = cursor.fetchone()
            new_id = res[0]
            new_date = res[1]
    
            if new_id <= 0:
                return None
    
            self.connection.commit()
    
            new_comment = AnnouncementComment(new_id, announcement_id, commenter_id, comment_text, str(new_date))
            return new_comment
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return None
        finally:
            if cursor and not cursor.closed:
                cursor.close()
    
    def get_comments(self, announcement_id: int) -> list[AnnouncementComment]:
        """
        Get all comments under a certain announcement.
        :param announcement_id: The ID of the announcement
        :return: A list of all comments under the announcement
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM announcement_comments WHERE announcement_id = %s", [announcement_id])

            comments = []
            for record in cursor:
                comment = AnnouncementComment(record[0], record[1], record[2], record[3], record[4])
                comments.append(comment)

            self.connection.commit()
            return comments
        except pg.Error as ex:
            self.connection.rollback()
            print(ex)
            return []
        finally:
            if cursor and not cursor.closed:
                cursor.close()
