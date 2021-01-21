import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from .db_builder import search_methods, blog_methods, pageEntries
from .auth import login_required

bp = Blueprint('search', __name__)

@bp.route("/search-results/<int:pageNum>", methods=["GET", "POST"])
@bp.route("/search-results", defaults={'pageNum': 1}, methods=["GET", "POST"])
@login_required
def searchFunction(pageNum):
    # if user submits search form
    if "search" in request.form:
        session["keywords"] = request.form["keywords"]

    if "keywords" in session:
        # if no keywords, reload page
        if session["keywords"].strip() == "":
            # reload home page
            return redirect(url_for("blog.homepage"))

        # return entries that have the keywords
        else:
            # get matching entries from db
            entries = [entry for entry in search_methods["search"](session["keywords"]) if blog_methods["getUsername"](entry["userID"]) is not None]
            for i in entries:
                # add username of creator to each entry
                i["username"] = blog_methods["getUsername"](i["userID"])
                # split post by new lines
                i["post"] = i["post"].split("\n")
            # if page doesn't exist, default to page 1
            entries = pageEntries(entries, 10)
            if len(entries) < pageNum or pageNum < 1:
                pageNum = 1
            return render_template("search/search-results.html", entries=entries,
                                    username=session["username"], pageNum=pageNum, search=session["keywords"])

    return redirect(url_for("blog.homepage"))

# when user clicks on an entry title from search results page
@bp.route("/home/blog/<int:ID>")
@login_required
def viewSearchResult(ID):
    # get userID
    userid = blog_methods["getEntryInfo"](ID, "userID")
    # get username
    username = blog_methods["getUsername"](userid)
    # return the blog of the user that posted entry
    return redirect(url_for("blog.viewBlog", username=username))