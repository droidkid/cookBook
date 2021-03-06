from cookBook import app
from flask import render_template, request, redirect, url_for, flash
from cloudinary.uploader import upload

import cookBook.datalayer.db as db
from cookBook.smdparser import parse
import cookBook.datalayer.postdao as PostDAO
import cookBook.datalayer.posttagdao as PostTagDAO
import cookBook.datalayer.tagdao as TagDAO
from cookBook.datalayer.post import Post
from config import *

PASS = ADMIN_PASS


def get_list_of_posturl(posts):
    list_of_posturl = ""
    post_link_builder = '-[link %s %s]'
    for post in posts:
        params = (post.get_title(), url_for("post", post_code=post.get_code()))
        list_of_posturl = list_of_posturl + (post_link_builder % params) + "\n"
    return list_of_posturl


def get_list_of_tagurl(tags):
    list_of_tagurl = ""
    tag_link_builder = '[link %s %s]'
    for tag in tags:
        params = (tag, url_for("tag", tagCode=tag))
        list_of_tagurl = list_of_tagurl + (tag_link_builder % params) + ', '
    return "Tags: " + list_of_tagurl[0:-2]


@app.route('/')
def index():
    posts = PostDAO.get_all_post_code(db.get_db())
    tags = TagDAO.get_all_tag(db.get_db())
    list_of_post = get_list_of_posturl(posts)
    list_of_tag = get_list_of_tagurl(tags)
    content = parse(list_of_tag + "\n\n" + list_of_post)
    return render_template('./index.html',
                           title='droidkid\'s blog',
                           postTitle='Posts',
                           postContent=content,
                           displayTag=False)


def edit_post(post_code, post_title, post_content, tag_list):
    post = Post()
    post.set_code(post_code)
    post.set_title(post_title)
    post.set_content(post_content)
    rows_changed = PostDAO.update_post(db.get_db(), post)
    if rows_changed == 0:
        PostDAO.insert_post(db.get_db(), post)
    TagDAO.add_tags(db.get_db(), tag_list)
    PostTagDAO.delete_tags_of_post(db.get_db(), post.get_code())
    PostTagDAO.update_tags_of_post(db.get_db(), post.get_code(), tag_list)
    TagDAO.remove_unused_tags(db.get_db())


@app.route('/edit/<post_code>', methods=['GET', 'POST'])
def edit(post_code):
    post_title = ''
    post_content = ''
    tags = ''
    if request.method == 'POST':
        post_title = request.form.get('postTitle').strip()
        post_content = request.form.get('postContent')
        tags = request.form.get('tags')
        tag_list = [tag for tag in tags.split(",")]
        filter(None, tag_list)
        password = request.form.get('password')
        if(password != PASS):
            flash('Wrong Password')
        elif not post_title:
            flash('Cannot Have Empty Post Title')
        else:
            edit_post(post_code, post_title, post_content, tag_list)
            return redirect(url_for('post', post_code=post_code))
    if request.method == 'GET':
        post = PostDAO.get_post(db.get_db(), post_code)
        tag_list = TagDAO.get_tag_of_post(db.get_db(), post_code)
        if post:
            post_code = post.get_code()
            post_title = post.get_title()
            post_content = post.get_content()
            tags = ",".join(tag_list)
    return render_template('./edit.html',
                           title=post_code,
                           postTitle=post_title,
                           postContent=post_content.rstrip(),
                           password='',
                           tags=tags)


@app.route('/post/<post_code>')
def post(post_code):
    post = PostDAO.get_post(db.get_db(), post_code)
    title = 'Lost?'
    content = 'Add a new page [link here /edit/'+post_code+']'
    displayTag = False
    tag_list = []
    if post:
        title = post.get_title()
        content = post.get_content()
        tag_list = TagDAO.get_tag_of_post(db.get_db(), post_code)
        displayTag = True
    return render_template('./post.html',
                           title=post_code,
                           postCode=post_code,
                           postTitle=title, tagList=tag_list,
                           postContent=parse(content),
                           displayTag=displayTag)


@app.route('/delete/<post_code>', methods=["POST"])
def delete(post_code):
    password = request.form.get('password')
    if password == PASS:
        result = PostDAO.delete_post(db.get_db(), post_code)
        if (result):
            flash('Post deleted')
        else:
            flash('Post does not exist')
        return redirect(url_for('index'))
    else:
        flash('Wrong Password')
        return redirect(url_for('edit', post_code=post_code))


@app.route('/tag/<tagCode>')
def tag(tagCode):
    posts = PostDAO.get_post_from_tag(db.get_db(), tagCode)
    list_of_posturl = get_list_of_posturl(posts)
    return render_template('./post.html',
                           title="tag- "+tagCode,
                           postTitle=tagCode,
                           displayTag=False,
                           postContent=parse(list_of_posturl))


@app.route('/upload_image', methods=["POST", "GET"])
def upload_image():
    if request.method == "POST":
        image_code = request.form.get('imageCode').strip()
        password = request.form.get('password')
        image = request.files['image']
        if image_code == "":
            flash('No empty fileName')
        elif password != PASS:
            flash('Invalid Password')
        else:
            try:
                upload_result = upload(image, public_id=image_code)
                if 'error' in upload_result:
                    flash(' error uploading ' + upload_result['error'])
                else:
                    flash(' image uploaded ')
            except:
                flash(' error. Please check file uploaded ')
    return render_template('./image.html', title="upload image")
