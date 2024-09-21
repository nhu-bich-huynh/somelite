import psycopg
from enum import IntEnum, auto
from werkzeug.security import generate_password_hash
from faker import Faker
import random

fake = Faker()


class Relation(IntEnum):
    friends = auto()


class Db:
    def __init__(
        self,
        name,
        user=None,
        password=None,
        admin_user="postgres",
        admin_password=None,
    ):
        self.name = name

        if user:
            self.user = user
        else:
            self.user = name

        if password:
            self.password = password
        else:
            self.password = name

        self.admin_user = admin_user

        if admin_password:
            self.admin_password = admin_password
        else:
            self.admin_password = admin_user

    def delete(self):
        with psycopg.connect(
            "dbname={} user={} password={}".format(
                self.admin_user, self.admin_user, self.admin_password
            )
        ) as conn:
            conn.autocommit = True

            with conn.cursor() as cur:
                try:
                    cur.execute("DROP DATABASE {}".format(self.name))
                except psycopg.ProgrammingError:
                    pass

                try:
                    cur.execute("DROP USER {}".format(self.user))
                except psycopg.ProgrammingError:
                    pass

    def create(self):
        with psycopg.connect(
            "dbname={} user={} password={}".format(
                self.admin_user, self.admin_user, self.admin_password
            )
        ) as conn:
            conn.autocommit = True

            with conn.cursor() as cur:
                cur.execute(
                    "CREATE USER {} WITH PASSWORD '{}'".format(self.user, self.password)
                )

                cur.execute("CREATE DATABASE {} OWNER {}".format(self.name, self.user))

    def connect(self):
        conn = psycopg.connect(
            "dbname={} user={} password={}".format(self.name, self.user, self.password)
        )
        conn.autocommit = True

        return conn

    def create_tables(self):
        with self.connect() as conn:
            conn.autocommit = True

            with conn.cursor() as cur:
                cur.execute("""CREATE TABLE users (
                                id serial PRIMARY KEY,
                                name text,
                                email text,
                                password text,
                                age integer
                            )
                            """)

                cur.execute("""
                            CREATE TABLE groups (
                                id serial PRIMARY KEY,
                                user_id integer REFERENCES users(id) ON DELETE CASCADE,
                                name text
                            )
                            """)

                cur.execute("""
                            CREATE TABLE posts (
                                id serial PRIMARY KEY,
                                user_id integer REFERENCES users(id) ON DELETE CASCADE,
                                date TIMESTAMP,
                                message text
                            )
                            """)

                cur.execute("""
                            CREATE TABLE relationships (
                                user_id_1 integer REFERENCES users(id) ON DELETE CASCADE,
                                user_id_2 integer REFERENCES users(id) ON DELETE CASCADE,
                                PRIMARY KEY (user_id_1, user_id_2),
                                CHECK (user_id_1 < user_id_2),
                                type integer
                            )
                            """)

                cur.execute("""
                            CREATE TABLE group_memberships (
                                user_id integer REFERENCES users(id) ON DELETE CASCADE,
                                group_id integer REFERENCES groups(id) ON DELETE CASCADE,
                                PRIMARY KEY (user_id, group_id)
                            )
                            """)

                cur.execute("""
                            CREATE TABLE likes (
                                user_id integer REFERENCES users(id) ON DELETE CASCADE,
                                post_id integer REFERENCES posts(id) ON DELETE CASCADE,
                                PRIMARY KEY (user_id, post_id)
                            )
                            """)

                self.insert_placeholder_data(20)

    def create_user(self, name, email, password, age):
        hash_pass = generate_password_hash(password)

        with self.connect().cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email, password, age) VALUES (%s, %s, %s, %s)",
                (name, email, hash_pass, age),
            )

    def add_post(self, user_id, date="CURRENT_TIMESTAMP", message=""):
        with self.connect().cursor() as cur:
            cur.execute(
                """INSERT INTO posts (user_id, date, message)
                    VALUES ('{}', {}, '{}')""".format(user_id, date, message)
            )

    def delete_post(self, post_id):
        with self.connect().cursor() as cur:
            cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))

    def get_user(self, id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                        SELECT *
                        FROM users
                        WHERE id = %s
                        """,
                (id,),
            )

            return cur.fetchone()

    def get_user_by_email(self, email):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                        SELECT *
                        FROM users
                        WHERE email = %s
                        """,
                (email,),
            )
    
            return cur.fetchone()

    def delete_user(self, id):
        with self.connect().cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (id,))

    def get_users(self):
        with self.connect().cursor() as cur:
            cur.execute("SELECT * FROM users")

            return cur.fetchall()

    def get_posts(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            SELECT *
                            FROM posts
                            """)

                return cur.fetchall()

    def get_names_and_posts(self):
        with self.connect().cursor() as cur:
            cur.execute("""
                        SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                        FROM users
                        JOIN posts ON users.id = posts.user_id
                        """)
            
            return cur.fetchall()

    def get_posts_of_user(self, id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                        SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                        FROM users
                        JOIN posts ON users.id = posts.user_id
                        WHERE users.id = %s
            """,
                (id,),
            )

            return cur.fetchall()

    def get_posts_of_friends(self, id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                FROM posts
                JOIN users
                ON posts.user_id = users.id
                WHERE posts.user_id IN (
                    SELECT user_id_1
                    FROM relationships
                    WHERE user_id_2 = %(id)s
                )
                OR posts.user_id IN (
                    SELECT user_id_2
                    FROM relationships
                    WHERE user_id_1 = %(id)s
                );
            """,
                {"id": id},
            )

            return cur.fetchall()

    def add_relation(self, user_id_1, user_id_2, relation_type):
        with self.connect().cursor() as cur:
            # Check if the relationship already exists
            cur.execute(
                "SELECT * FROM relationships WHERE user_id_1 = %s AND user_id_2 = %s",
                (user_id_1, user_id_2),
            )
            relationship = cur.fetchone()
            if not relationship:
                cur.execute(
                    "INSERT INTO relationships (user_id_1, user_id_2, type) VALUES (%s, %s, %s)",
                    (user_id_1, user_id_2, relation_type),
                )

    def insert_placeholder_data(self, n):
        # Create fixed users
        self.create_user("alice", "alice@alice", "alice", 30)
        self.create_user("bob", "bob@bob", "bob", 35)
        self.create_user("charlie", "charlie@charlie", "charlie", 25)
        self.create_user("david", "david@david", "david", 40)

        # Generate random users
        for _ in range(5, n + 1):
            first_name = fake.first_name()
            name = first_name
            email = fake.email()
            password = name  # fake.password()
            age = random.randint(18, 80)
            self.create_user(name, email, password, age)

        # Inserting fixed data into the 'groups' table
        self.add_group(1, "Staff")
        self.add_group(2, "Student")
        self.add_group(3, "Alumni")

        # Inserting fixed data into the 'posts' table
        self.add_post(1, message="Hello, world!")
        self.add_post(2, message="This is a test post.")
        self.add_post(3, message="Welcome to my domain!")
        self.add_post(4, message="Test post, please ignore")

        # Generate random data into the 'posts' table
        for i in range(5, n + 1):
            post_message = fake.text()
            self.add_post(i, message=post_message)

        # Adding fixed relationships
        self.add_relation(1, 2, Relation.friends)
        self.add_relation(1, 3, Relation.friends)

        # Adding random relationships
        max_relationships_per_user = 5
        pairs = [
            (user_id_1, user_id_2)
            for user_id_1 in range(1, n)
            for user_id_2 in range(user_id_1 + 1, n + 1)
        ]
        random.shuffle(pairs)

        relationships_per_user = {user_id: 0 for user_id in range(1, n + 1)}

        for user_id_1, user_id_2 in pairs:
            if (
                relationships_per_user[user_id_1] < max_relationships_per_user
                and relationships_per_user[user_id_2] < max_relationships_per_user
            ):
                self.add_relation(user_id_1, user_id_2, Relation.friends)
                relationships_per_user[user_id_1] += 1
                relationships_per_user[user_id_2] += 1

        # Creating fixed groups
        self.add_group(2, "Bob og Charlie's gruppe")

        # Creating random groups
        for user_id in range(1, 10):
            group_name = fake.company()
            self.add_group(user_id, group_name)

        # Adding fixed Group Memberships
        self.join_group(1, 1)
        self.join_group(1, 2)
        self.join_group(2, 4)
        self.join_group(3, 4)

        # Adding random group memberships
        for user_id in range(1, n):
            group_id = random.randint(1, 10)
            self.join_group(user_id, group_id)

        # Adding some likes
        self.like_post(1, 1)
        self.like_post(1, 1)
        self.like_post(1, 2)
        self.like_post(3, 1)
        self.like_post(2, 3)
        self.like_post(1, 4)

        print("Test : ", self.get_posts_of_groups_ordered(2))

    def remove_relation(self, user_id_1, user_id_2):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM relationships WHERE user_id_1 = %s AND user_id_2 = %s",
                    (user_id_1, user_id_2),
                )

    def add_group(self, owner_id, namex):
        with self.connect().cursor() as cur:
            cur.execute(
                "INSERT INTO groups (user_id, name) VALUES (%s, %s)", (owner_id, namex)
            )

    def delete_group(self, owner_id):
        with self.connect().cursor() as cur:
            cur.execute("DELETE FROM groups WHERE user_id = %s", (owner_id,))

    def join_group(self, user_id, group_id):
        with self.connect().cursor() as cur:
            # Check if the membership already exists
            cur.execute(
                "SELECT * FROM group_memberships WHERE user_id = %s AND group_id = %s",
                (user_id, group_id),
            )
            existing_membership = cur.fetchone()
            if not existing_membership:
                # Insert the new membership if it doesn't exist
                cur.execute(
                    "INSERT INTO group_memberships (user_id, group_id) VALUES (%s, %s)",
                    (user_id, group_id),
                )

    def leave_group(self, user_id, group_id):
        with self.connect().cursor() as cur:
            cur.execute(
                "DELETE FROM group_memberships WHERE user_id = %s AND group_id = %s",
                (user_id, group_id),
            )

    def like_post(self, user_id, post_id):
        with self.connect().cursor() as cur:
            cur.execute(
                "INSERT INTO likes (user_id, post_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",  # if a duplicate like is attempted, the insertion is ignored
                (user_id, post_id),
            )

    def show_all_likes(self, post_id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                        SELECT COUNT(likes.user_id) AS like_count
                        FROM likes
                        WHERE likes.post_id = %s;
                        """,
                (post_id,),
            )
            return cur.fetchone()[0]

    def regular_match(self, keyword):
        with self.connect().cursor() as cur:
            words = keyword.split()
            pattern = "|".join(words)
            query = """
                SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                FROM posts
                JOIN users ON posts.user_id = users.id
                WHERE posts.message ~* %s;
            """
            cur.execute(query, (pattern,))
            return cur.fetchall()

    # Given a group id, returns all the posts made by its members
    def get_posts_of_group(self, groupid):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                FROM posts
                JOIN users
                ON posts.user_id = users.id
                WHERE posts.user_id IN (
                    SELECT user_id
                    FROM group_memberships
                    WHERE group_id = %(groupid)s
                );
            """,
                {"groupid": groupid},
            )
            return cur.fetchall()

    # Given a user_id, returns all the posts made by people who share a group with that person
    def get_posts_of_groups(self, user_id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                SELECT users.name, posts.id, posts.user_id, posts.date, posts.message
                FROM posts
                JOIN users
                ON posts.user_id = users.id
                WHERE posts.user_id IN (
                    SELECT user_id
                    FROM group_memberships
                    WHERE group_id IN(
                        SELECT group_id
                        FROM group_memberships
                        WHERE user_id = %(user_id)s
                    )
                )
                """,
                {"user_id": user_id},
            )
            return cur.fetchall()

    # Given a group ID, returns the name of the corresponding group
    def get_name_of_group(self, group_id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                SELECT name
                FROM groups
                WHERE id = %(group_id)s
                """,
                {"group_id": group_id},
            )
            return cur.fetchone()

    # Returns a list of the names of groups a given user is a member of, and the posts made by their members
    def get_posts_of_groups_ordered(self, user_id):
        with self.connect().cursor() as cur:
            cur.execute(
                """
                SELECT group_id
                FROM group_memberships
                WHERE user_id = %s
                """,
                (user_id,),
            )
            group_ids = cur.fetchall()

            result = []
            for id in group_ids:
                posts = Db.get_posts_of_group(self, (id[0]))
                name = Db.get_name_of_group(self, id[0])
                result.append((posts, name[0]))

            return result
