from post import Post

class Util:
    def convert_to_web(names_posts):
        names = []
        posts = []
        for name, *post in names_posts:
            names.append(name.capitalize())
            posts.append(Post(*post))

        return (names, posts)
