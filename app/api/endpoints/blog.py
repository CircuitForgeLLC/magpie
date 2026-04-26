from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.directus import get_blog_post, publish_blog_post, update_blog_post

router = APIRouter(prefix="/blog", tags=["blog"])


class PublishRequest(BaseModel):
    title: str
    body: str
    slug: str | None = None
    tags: list[str] | None = None
    author: str | None = None
    seo_description: str | None = None
    published_at: str | None = None  # ISO 8601; defaults to now


class UpdateRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    seo_description: str | None = None
    published_at: str | None = None


@router.post("", summary="Publish a blog post to the CircuitForge website via Directus")
def publish(req: PublishRequest) -> dict:
    try:
        item = publish_blog_post(
            title=req.title,
            body=req.body,
            slug=req.slug,
            tags=req.tags,
            author=req.author,
            seo_description=req.seo_description,
            published_at=req.published_at,
        )
        return {"ok": True, "post": item}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{slug}", summary="Fetch a blog post by slug")
def get_post(slug: str) -> dict:
    post = get_blog_post(slug)
    if post is None:
        raise HTTPException(status_code=404, detail=f"No blog post with slug '{slug}'")
    return post


@router.patch("/{post_id}", summary="Update an existing blog post by Directus ID")
def update(post_id: int, req: UpdateRequest) -> dict:
    fields = req.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        item = update_blog_post(post_id, fields)
        return {"ok": True, "post": item}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
