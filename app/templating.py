from pathlib import Path

from fastapi.templating import Jinja2Templates

HERE = Path(__file__).parent

templates = Jinja2Templates(directory=HERE / "templates")

# browsers hang on to old css files. putting the file's last-modified time in the url
# (/static/style.css?v=...) means they download it again whenever it changes
templates.env.globals["css_version"] = int((HERE / "static" / "style.css").stat().st_mtime)
