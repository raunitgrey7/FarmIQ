from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from backend.community.models import CommunityPost, Comment
from backend.database.db import get_db

import os
from uuid import uuid4
from datetime import datetime
import humanize

router = APIRouter()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ View Community Page
@router.get("/community", response_class=HTMLResponse)
def view_community(request: Request, db: Session = Depends(get_db)):
    posts = db.query(CommunityPost).order_by(CommunityPost.created_at.desc()).all()

    now = datetime.utcnow()
    for post in posts:
        if post.created_at:
            post.time_ago = humanize.naturaltime(now - post.created_at)
        else:
            post.time_ago = "Just now"

        for comment in post.comments:
            if comment.created_at:
                comment.time_ago = humanize.naturaltime(now - comment.created_at)
            else:
                comment.time_ago = "Just now"

    return request.app.templates.TemplateResponse("community.html", {"request": request, "posts": posts})


# ✅ Create New Post
@router.post("/community/post")
async def create_post(
    name: str = Form("Anonymous"),
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(await image.read())
        image_path = f"/static/uploads/{filename}"

    post = CommunityPost(
        name=name,
        title=title,
        content=content,
        category=category,
        image_path=image_path,
        created_at=datetime.utcnow()  # 🔄 ensure created_at is set
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return RedirectResponse(url="/community", status_code=303)


# ✅ Add Comment to a Post
@router.post("/community/comment/{post_id}")
async def add_comment(
    post_id: int,
    commenter: str = Form("Anonymous"),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    comment = Comment(
        post_id=post_id,
        commenter=commenter,
        content=content,
        created_at=datetime.utcnow()  # 🔄 ensure comment timestamp
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return RedirectResponse(url="/community", status_code=303)


# ✅ Delete a Post
@router.post("/community/delete/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()
    return RedirectResponse(url="/community", status_code=303)
