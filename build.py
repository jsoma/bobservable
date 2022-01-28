from pathlib import Path
import mimetypes
from jinja2 import Template
import shutil
import markdown
import frontmatter
from natsort import natsorted
import filecmp
import subprocess

CONTENT_DIR = Path('./content')
STATIC_DIR = Path('./static')
RENDER_DIR = Path('./docs')

shutil.rmtree(RENDER_DIR, ignore_errors=True)

dirs = [dir for dir in CONTENT_DIR.glob('*/*/') if dir.is_dir()]

with open('page.html') as f:
    page_template = Template(f.read(), autoescape=True)

with open('diff.html') as f:
    diff_template = Template(f.read(), autoescape=True)

class Page:

    def __init__(self, dir):
        self.dir = dir
        self.full_name = self.dir.relative_to(CONTENT_DIR)
        self.render_dir = RENDER_DIR.joinpath(self.full_name)

    def get_versions(self):
        versions = [Version(dir) for dir in self.dir.glob('*/') if dir.is_dir()]
        self.versions = natsorted(versions, key=lambda v: v.version_name)[::-1]
    
    def get_version_names(self):
        return [v.version_name for v in self.versions]

    def build_versions(self):
        self.get_versions()

        version_names = self.get_version_names()
        for v in self.versions:
            v.build(version_names)
    
    def populate_latest(self):
        latest_version = self.versions[0]

        latest_path = self.render_dir.joinpath('latest')

        # latest_path.symlink_to(latest_version.version_name, target_is_directory=True)
        shutil.copytree(latest_version.render_dir, latest_path)

        self.render_dir.joinpath("index.html").write_text(f"""
        <meta http-equiv="refresh" content="0; url=./latest" />
        """)
    
    def compute_diffs(self):
        diff_dir = self.render_dir.joinpath('diff')
        diff_dir.mkdir(parents=True, exist_ok=True)

        for source in self.versions:
            for target in self.versions:
                process = subprocess.run(['diff', '-u', target.dir, source.dir], 
                         stdout=subprocess.PIPE, 
                         universal_newlines=True)

                diff_dir.joinpath(f"{source.version_name}-{target.version_name}.diff").write_text(process.stdout)
        
        version_names = self.get_version_names()
        html = diff_template.render(version_names=version_names)
        diff_dir.joinpath('index.html').write_text(html)


class Version:

    def __init__(self, dir):
        self.dir = dir
        self.version_name = dir.name
        self.full_name = self.dir.parent.relative_to(CONTENT_DIR)

        self.render_dir = RENDER_DIR.joinpath(self.full_name).joinpath(self.version_name)
        self.raw_dir = self.render_dir.joinpath("raw")
        self.readme = None
        self.title = None
    
    def read_readme(self):
        try:
            path = self.dir.joinpath("README.md")
            post = frontmatter.load(path)
            readme = markdown.markdown(post.content)
            if 'title' in post.metadata:
                self.title = post.metadata['title']
            self.readme = readme
        except:
            pass

    def copy_files(self, target_dir=None):
        if target_dir is None:
            target_dir = self.raw_dir

        target_dir.mkdir(parents=True, exist_ok=True)
        paths = self.get_filelist()

        for path in paths:
            shutil.copy(path, target_dir)

    def get_filelist(self, include_readme=False):
        return [path for path in self.dir.glob('[!.]*') if (path.name != "README.md" or include_readme)]

    def read_files(self, populate_files=True):
        paths = self.get_filelist()

        self.files = []
        for path in paths:
            guess = mimetypes.guess_type(path)
            if guess[0] and guess[0].startswith("image"):
                self.files.append({ 'name': path.name, 'type': 'image'})
            else:
                try:
                    self.files.append({
                        'name': path.name,
                        'contents': path.read_text(),
                        'type': 'text',
                        'extension': path.suffix.replace(".", "")
                    })
                except:
                    print("Failed to read", path.name)

    def render_index(self, version_names):
        html = page_template.render(
            name=self.full_name,
            files=self.files,
            readme=self.readme,
            title=self.title,
            version_names=version_names,
            version_name=self.version_name
        )
    
        index = self.render_dir.joinpath("index.html")
        index.write_text(html)

    def build(self, version_names):
        self.read_readme()
        self.read_files()
        self.copy_files()
        self.render_index(version_names)


for dir in dirs:
    page = Page(dir)
    page.build_versions()
    page.populate_latest()
    page.compute_diffs()

for f in STATIC_DIR.glob("[!.]*"):
    shutil.copy(f, RENDER_DIR)
