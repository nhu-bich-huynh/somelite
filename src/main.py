from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import login_required, current_user

from util import Util
from app import db
from post import Post

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return redirect(url_for("main.home"))


@main.route("/home")
@login_required
def home():
    names_posts = db.get_posts_of_user(current_user.id)
    names, posts = Util.convert_to_web(names_posts)

    return render_template("home.html", names=names, posts=posts, user=current_user)


@main.route("/home", methods=["POST"])
@login_required
def home_post():
    like_post = request.form.get("like_post")
    delete_post = request.form.get("delete_post")
    message = request.form.get("message")
    delete_user = request.form.get("delete_account")

    if like_post:
        db.like_post(current_user.id, like_post)
    elif delete_post:
        db.delete_post(delete_post)
    elif message:
        db.add_post(current_user.id, message=message)
    elif delete_user:
        db.delete_user(current_user.id)

    return redirect(url_for("main.home"))


@main.route("/friends")
@login_required
def friends():
    names_posts = db.get_posts_of_friends(current_user.id)
    names, posts = Util.convert_to_web(names_posts)

    return render_template("main.html", names=names, posts=posts, user=current_user)


@main.route("/friends", methods=["POST"])
@login_required
def friends_post():
    like_post = request.form.get("like_post")
    delete_post = request.form.get("delete_post")
    search = request.form.get("search")

    if like_post:
        db.like_post(current_user.id, like_post)
    elif delete_post:
        db.delete_post(delete_post)
    elif search:
        names_posts = db.regular_match(search)
        names, posts = Util.convert_to_web(names_posts)
        return render_template("main.html", names=names, posts=posts, user=current_user)

    return redirect(url_for("main.friends"))


@main.route("/groups")
@login_required
def groups():
    groups = db.get_posts_of_groups_ordered(current_user.id)

    new = []
    for group in groups:
        posts, group_name = group

        new_posts = []
        for post in posts:
            (user_name, *without_name) = post
            obj = Post(*without_name)
            new_posts.append((user_name, obj))

        new.append((new_posts, group_name))
    groups = new

    key = request.args.get("key", None)
    if not key:
        posts = None
        if groups:
            posts = groups[0][0]

        return render_template(
            "groups.html", posts=posts, groups=groups, user=current_user
        )

    posts = None
    for group in groups:
        group_posts, name = group

        if key == name:
            posts = group_posts

    return render_template("groups.html", posts=posts, groups=groups, user=current_user)


@main.route("/groups", methods=["POST"])
@login_required
def groups_post():
    like_post = request.form.get("like_post")
    delete_post = request.form.get("delete_post")

    if like_post:
        db.like_post(current_user.id, like_post)
    elif delete_post:
        db.delete_post(delete_post)

    return redirect(url_for("main.groups", **request.args.to_dict()))
