from pathlib import Path
import mimetypes
from jinja2 import Template
import shutil
import markdown
import frontmatter

content_dir = Path('./content')
static_dir = Path('./static')
render_dir = Path('./docs')

shutil.rmtree(render_dir, ignore_errors=True)

dirs = [dir for dir in content_dir.glob('*/*/') if dir.is_dir()]

with open('page.html') as f:
    template = Template(f.read(), autoescape=True)

for dir in dirs:
    readme = None
    title = None
    paths = list(dir.glob('[!.]*'))

    files = []
    full_name = dir.relative_to(content_dir)
    output_dir = render_dir.joinpath(full_name)
    raw_dir = output_dir.joinpath("raw")

    raw_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        guess = mimetypes.guess_type(path)

        shutil.copy(path, raw_dir)

        if guess[0] and guess[0].startswith("image"):
            files.append({ 'name': path.name, 'type': 'image'})
        else:
            if path.name == "README.md":
                post = frontmatter.load(path)
                readme = markdown.markdown(post.content)
                if 'title' in post.metadata:
                    title = post.metadata['title']
                continue
            try:
                files.append({
                    'name': path.name,
                    'contents': path.read_text(),
                    'type': 'text',
                    'extension': path.suffix.replace(".", "")
                })
            except:
                print("Failed to read", path.name)

    html = template.render(name=full_name, files=files, readme=readme, title=title)
    
    index = output_dir.joinpath("index.html")
    index.write_text(html)

for f in static_dir.glob("[!.]*"):
    shutil.copy(f, render_dir)