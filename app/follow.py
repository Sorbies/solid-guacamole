import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from .db_builder import follow_methods, blog_methods
from .auth import login_required

bp = Blueprint('follow', __name__)

@bp.route("/follow/<string:username>", methods=["GET", "POST"])
@login_required
def follow(username):
    # if user not following blog
    if not follow_methods["checkFollower"](blog_methods["getInfo"](username, "id"), blog_methods["getInfo"](session["username"], "id")):
        # add blog to db
        follow_methods["addFollower"](blog_methods["getInfo"](username, "id"), blog_methods["getInfo"](session["username"], "id"))

        # set msg to following blog
        session["error_msg"] = "Successfully followed blog!"

        # if user follows blog from home page
        if "home" in request.form:
            # return home page with msg
            return redirect(url_for("blog.homepage"))

        # if user follows blog from blog page
        if "viewBlog" in request.form:
            # return blog page with msg
            return redirect(url_for("blog.viewBlog", pageNum=1, username=username))

    # if user following blog
    else:
        # if already following blog, set msg to that
        session["error_msg"] = "Already following blog."

        # if user unfollows blog from home page
        if "home" in request.form:
            # return home page with msg
            return redirect(url_for("blog.homepage"))

        # if user unfollows blog from blog page
        if "viewBlog" in request.form:
            # return blog page with msg
            return redirect(url_for("blog.viewBlog", pageNum=1, username=username))

@bp.route("/unfollow/<string:username>", methods=["GET", "POST"])
@login_required
def unfollow(username):
    # if user not following blog
    if not follow_methods["checkFollower"](blog_methods["getInfo"](username, "id"), blog_methods["getInfo"](session["username"], "id")):
        # set msg to not following blog, can't unfollow
        session["error_msg"] = "Not following this blog yet, cannot unfollow."

        # if user unfollows blog from home page
        if "home" in request.form:
            # return home page with msg
            return redirect(url_for("blog.homepage"))

        # if user unfollows blog from blog page
        if "viewBlog" in request.form:
            # return blog page with msg
            return redirect(url_for("blog.viewBlog", pageNum=1, username=username))

    # if user following blog
    else:
        # remove blog from db
        follow_methods["removeFollower"](blog_methods["getInfo"](username, "id"), blog_methods["getInfo"](session["username"], "id"))
        # if following blog, set msg to unfollowing
        session["error_msg"] = "Successfully unfollowed blog!"

        # if user unfollows blog from home page
        if "home" in request.form:
            # return home page with msg
            return redirect(url_for("blog.homepage"))

        # if user unfollows blog from blog page
        if "viewBlog" in request.form:
            # return blog page with msg
            return redirect(url_for("blog.viewBlog", pageNum=1, username=username))

        # if user unfollows blog from following blogs page
        if "followUnfollow" in request.form:
            # return following blog page with msg
            return redirect(url_for("follow.followedBlogs"))

@bp.route("/followed-blogs")
@login_required
def followedBlogs():
    # to prevent error if user is not following any blogs yet
    following = []
    # for each blog user is following
    for blog in follow_methods["getFollowedBlogs"](blog_methods["getInfo"](session["username"], "id")):
        # add blogname to list
        if blog is not None:
            following += [blog["blogname"]]
    # if user successfully unfollowed blog
    if "error_msg" in session:
        # store error
        msg = session["error_msg"]
        # remove error from session
        session.pop("error_msg")
        # return followed blogs
        return render_template("follow/follow-blog.html", blogs=follow_methods["getFollowedBlogs"](blog_methods["getInfo"](session["username"], "id")),
                                following=following, error_msg=msg, username=session["username"])
    # return followed blogs
    return render_template("follow/follow-blog.html", blogs=follow_methods["getFollowedBlogs"](blog_methods["getInfo"](session["username"], "id")),
                            following=following, username=session["username"])
