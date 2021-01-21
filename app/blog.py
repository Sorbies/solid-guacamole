from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from .auth import login_required
from .db_builder import auth_methods, blog_methods, follow_methods, validateInput, pageEntries

bp = Blueprint('blog', __name__)

@bp.route("/")
@login_required
def homepage():
    following = []
    # assign blank msg to avoid error
    # for each blog
    for blog in blog_methods["getBlogs"]():
        # if user is following the blog
        if follow_methods["checkFollower"](blog["id"], blog_methods["getInfo"](session["username"], "id")):
            # add blogname to list
            following += [blog["blogname"]]
    # if user successfully followed/unfollowed or already following/unfollowing blog
    if "error_msg" in session:
        # store error
        msg = session["error_msg"]
        # remove error from session
        session.pop("error_msg")
        # reload page with error
        return render_template("blog/home.html", blogs=blog_methods["getBlogs"](), following=following,
                                username=session["username"], error_msg=msg)
    # if user hasn't submitted follow/unfollow form yet, load home page
    return render_template("blog/home.html", blogs=blog_methods["getBlogs"](), following=following,
                            username=session["username"])

# end of url when viewing a blog is the users name
@bp.route("/home/blog/<string:username>/", defaults={'pageNum': 1})
@bp.route("/home/blog/<string:username>/<int:pageNum>")
@login_required
def viewBlog(username, pageNum):
    # check is user exists in db, if not return error page
    if not auth_methods["checkUsername"](username):
        return abort(404)

    # check is user is following blog
    following = follow_methods["checkFollower"](blog_methods["getInfo"](username, "id"), blog_methods["getInfo"](session["username"], "id"))

    # split by newlines in blog description and entry bodies
    blogdescription = blog_methods["getInfo"](username, "blogdescription").split("\n")

    # if user is the one who created the blog, set iscreator to True
    # otherwise, set iscreator to False
    iscreator = (session["username"] == username)

    # format entries for pageview
    entries = blog_methods["getEntries"](blog_methods["getInfo"](username, "id"))
    for i in entries:
        # splits by new lines in posts of the entries
        i["post"] = i["post"].split("\n")
    # make list of pages of entries
    entries = pageEntries(entries, 10)
    # if page doesn't exist, default to page 1
    if len(entries) < pageNum or pageNum < 1:
        pageNum = 1

    # checks if follow/unfollow related message in session
    if "error_msg" in session:
        # store error
        msg = session["error_msg"]
        # remove error from session
        session.pop("error_msg")
        # returns home page with error
        return render_template("blog/blog.html", blogname=blog_methods["getInfo"](username, "blogname"), blogdescription=blogdescription,
                                creator=username, iscreator=iscreator, entries=entries, pageNum=pageNum,
                                error_msg=msg, following=following, username=session["username"])

    # show blog with all info received from db
    return render_template("blog/blog.html", blogname=blog_methods["getInfo"](username, "blogname"), blogdescription=blogdescription,
                            creator=username, iscreator=iscreator, entries=entries, pageNum=pageNum,
                            following=following, username=session["username"])  # get id of username from url

@bp.route("/edit-blog/<int:pageNum>", methods=["GET", "POST"])
@bp.route("/edit-blog", defaults={'pageNum': 1}, methods=["GET", "POST"])
@login_required
def editBlog(pageNum):
    entries = pageEntries(blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id")), 10)
    if len(entries) < pageNum or pageNum < 1:
        pageNum = 1

    # if user has submitted the form
    if "blog" in request.form:
        # check if blog name and blog description are valid
        error_msg = []
        blogname = validateInput("blogname", request.form["blogname"], error_msg)
        blogdescription = validateInput("blogdescription", request.form["blogdescription"], error_msg)

        # if an error occured
        if len(error_msg) > 0:
            # return template with username from session, original blogname, new description, add entry content,
            # old editable entries, and error msg
            return render_template("blog/edit-blog.html", username=session["username"],
                                    blogname=blog_methods["getInfo"](session["username"], "blogname"),
                                    blogdescription=request.form["blogdescription"], entries=entries,
                                    error_msg=error_msg[0], pageNum=pageNum)

        # otherwise blog name and blog description are valid
        # update blog name/description
        blog_methods["updateBlogInfo"](session["username"], blogname, blogdescription)
        # want to display success msg first, then view blog
        error_msg = "Successfully updated blog name and description!"
        return render_template("blog/edit-blog.html", username=session["username"],
                                blogname=request.form["blogname"],
                                blogdescription=request.form["blogdescription"],
                                entries=entries, error_msg=error_msg, pageNum=pageNum)

    # if user submits add entry form
    if "addEntry" in request.form:
        # check if entry title, picture, and content are valid
        error_msg = []
        entrytitle = validateInput("entrytitle", request.form["title"], error_msg)
        entrycontent = validateInput("entrycontent", request.form["content"], error_msg)
        entrypic = validateInput("entrypic", request.form["pic"], error_msg)
        if len(error_msg) > 0:
            # return template with information filled in and error msg
            return render_template("blog/edit-blog.html", username=session["username"],
                                    blogname=blog_methods["getInfo"](session["username"], "blogname"),
                                    blogdescription=blog_methods["getInfo"](session["username"], "blogdescription"),
                                    entrycontent=request.form["content"], entrytitle=request.form["title"],
                                    error_msg=error_msg[0],
                                    entries=pageEntries(blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id")), 10))

        # if user has entry title and content
        else:
            # get user id from db (since user is editing, username is from session)
            userID = blog_methods["getInfo"](session["username"], "id")
            # add entry to db
            blog_methods["addEntry"](userID, entrytitle, entrycontent, entrypic)
            # if entry is properly filled out, return template with forms filled out and success msg
            return render_template("blog/edit-blog.html", username=session["username"],
                                    blogname=blog_methods["getInfo"](session["username"], "blogname"),
                                    blogdescription=blog_methods["getInfo"](session["username"], "blogdescription"),
                                    error_msg="Successfully added entry!",
                                    entries=pageEntries(blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id")), 10))

    # if user submits edit entry form
    if "editEntry" in request.form:
        # if there was an error message
        if session["error_msg"] and session["error_msg"] != "":
            # store error
            msg = session["error_msg"]
            # remove from session
            session.pop("error_msg")
            # return template with blog info and entry info filled in, and an error msg
            return render_template("blog/edit-blog.html", username=session["username"],
                                    blogname=blog_methods["getInfo"](session["username"], "blogname"),
                                    blogdescription=blog_methods["getInfo"](session["username"], "blogdescription"), error_msg=msg,
                                    entries=pageEntries(blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id")), 10))

    # if user submits delete entry form
    if "deleteEntry" in request.form:
        if session["error_msg"] and session["error_msg"] == "Successfully deleted entry!":
            # store error
            msg = session["error_msg"]
            # remove from session
            session.pop("error_msg")
            # return template with blog info and entry info filled in, and an error msg
            return render_template("blog/edit-blog.html", username=session["username"],
                                    blogname=blog_methods["getInfo"](session["username"], "blogname"),
                                    blogdescription=blog_methods["getInfo"](session["username"], "blogdescription"), error_msg=msg,
                                    entries=pageEntries(blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id")), 10))

    # if user hasn't submitted forms yet, load page with blog name/desc from db, and all entries
    return render_template("blog/edit-blog.html", username=session["username"],
                            blogname=blog_methods["getInfo"](session["username"], "blogname"),
                            blogdescription=blog_methods["getInfo"](session["username"], "blogdescription"),
                            entries=entries, pageNum=pageNum)

# end of url when viewing a blog is the entry id
@bp.route("/edit/<int:entryID>", methods=["GET", "POST"])
@login_required
def editEntries(entryID):
    # get a list of entries that the user owns
    userEntries = [entry["id"] for entry in blog_methods["getEntries"](blog_methods["getInfo"](session["username"], "id"))]

    # check if user owns entry they are trying to edit (if user changes url)
    if entryID in userEntries:
        # if user clicks on edit entry
        if "editEntry" in request.form:
            # check if entry title, picture, and content are valid
            error_msg = []
            entrytitle = validateInput("entrytitle", request.form["title"], error_msg)
            entrycontent = validateInput("entrycontent", request.form["content"], error_msg)
            entrypic = validateInput("entrypic", request.form["pic"], error_msg)
            if len(error_msg) > 0:
                # sets msg for edit-blog
                session["error_msg"] = error_msg[0]
                # redirects to edit-blog page with msg
                return redirect(url_for("blog.editBlog", pageNum=1), code=307)

            # entry title and content cannot be unchanged
            elif (entrytitle == blog_methods["getEntryInfo"](entryID, "title")) \
                    and (entrycontent == blog_methods["getEntryInfo"](entryID, "post")) \
                    and (entrypic == blog_methods["getEntryInfo"](entryID, "pic")):
                # sets msg for edit-blog
                session["error_msg"] = "No changes made to entry title or content"
                # redirects to edit-blog page with msg
                return redirect(url_for("blog.editBlog", pageNum=1), code=307)

            # both are changed and not blank
            else:
                # if no error, edit entry and reload page with new entry
                blog_methods["editEntry"](entryID, entrytitle, entrycontent, entrypic)
                # sets msg for edit-blog
                session["error_msg"] = "Successfully updated entry!"
                # redirects to edit-blog page with msg
                return redirect(url_for("blog.editBlog", pageNum=1), code=307)

        # if user submits delete entry form
        elif "deleteEntry" in request.form:
            # delete the entry and reload page
            blog_methods["deleteEntry"](entryID)
            # sets msg for edit-blog
            session["error_msg"] = "Successfully deleted entry!"
            # redirects to edit-blog page with msg
            return redirect(url_for("blog.editBlog", pageNum=1), code=307)
        # user owns entry but has not submitted any forms yet
        return redirect(url_for("blog.editBlog"))
    # user does not own entry they are attempting to create
    return redirect(url_for("blog.editBlog"))
