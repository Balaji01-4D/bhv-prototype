from fastapi import FastAPI, Request, UploadFile, Form, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from github import Github
from github.GithubException import GithubException

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/images", response_class=HTMLResponse)
async def upload_image(request: Request, file: UploadFile = File(...), narrative: str = Form(...)):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise HTTPException(status_code=500, detail="GitHub token or repository not configured")

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        content = await file.read()
        path = f"images/{file.filename}"
        result = repo.create_file(path, f"Add image {file.filename}", content, branch="main")
        narrative_result = repo.create_file(path + ".txt", f"Add narrative for {file.filename}", narrative.encode(), branch="main")

        image_url = result["content"].html_url
        narrative_url = narrative_result["content"].html_url
        return templates.TemplateResponse("success.html", {"request": request, "image_url": image_url, "narrative_url": narrative_url})
    except GithubException as e:
        raise HTTPException(status_code=500, detail=f"GitHub error: {e.data}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
