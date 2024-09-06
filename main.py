import sys
import os
import hashlib
import requests
import shutil
import stat
from urllib.parse import urlparse, urljoin
from sympy import preview  # For rendering LaTeX equations as images
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from lxml import etree  # For parsing XML-like syntax

def ensure_tmp_directory():
    # Define the output directory for temporary images
    output_dir = os.path.join(os.path.dirname(__file__), "tmp")  # Make 'tmp' relative to the script's location

    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Ensure the directory has the correct permissions
    os.chmod(output_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # Read, write, and execute for everyone

    return output_dir

class PyMLRenderer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the base URL for GitHub repository
        self.base_url = None

        # Ensure LaTeX is in the PATH
        latex_path = shutil.which("latex")  # Check if LaTeX is in the current PATH
        dvipng_path = shutil.which("dvipng")

        if not latex_path or not dvipng_path:
            if sys.platform == "win32":
                # Example path for MiKTeX on Windows
                os.environ["PATH"] += ";C:\\Program Files\\MiKTeX\\miktex\\bin\\x64"
            elif sys.platform == "darwin":
                # Example path for MacTeX on macOS
                os.environ["PATH"] += ":/Library/TeX/texbin"
            elif sys.platform.startswith("linux"):
                # Example path for TeX Live on Linux
                os.environ["PATH"] += ":/usr/local/texlive/2023/bin/x86_64-linux"
        else:
            print(f"LaTeX found at {latex_path}")

        self.setWindowTitle("Galacton - PyML Renderer")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        layout = QVBoxLayout()

        # Web view for displaying content
        self.web_view = QWebEngineView()
        self.web_view.urlChanged.connect(self.handle_link_click)
        layout.addWidget(self.web_view)

        # Central widget setup
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Load initial PyML content from a file
        self.load_pyml_file("https://raw.githubusercontent.com/RadEZorack/Galacton/main/index.pyml")



    def load_pyml_file(self, file_path):
        try:
            # Check if the path is a URL
            parsed_url = urlparse(file_path)
            if parsed_url.scheme in ['http', 'https']:
                # Fetch content from the URL
                response = requests.get(file_path)
                response.raise_for_status()  # Check for HTTP errors
                pyml_content = response.text
                self.base_url = os.path.dirname(file_path) + '/'  # Store base URL for resolving relative links
            else:
                # Load content from a local file
                with open(file_path, 'r') as file:
                    pyml_content = file.read()

            # Parse and render the PyML content
            self.parse_pyml(pyml_content)

        except Exception as e:
            self.web_view.setHtml(f"<p>Error loading PyML: {e}</p>")


    def parse_pyml(self, pyml_content):
        try:
            # Parse the .pyml content
            root = etree.fromstring(pyml_content)

            # Start building the HTML content
            content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>PyML Renderer</title>
            </head>
            <body>
            """

            # Process elements
            for element in root.iter():
                if element.tag == 'header':
                    content += f"<h1>{element.text}</h1>\n"
                elif element.tag == 'p':
                    content += f"<p>{element.text}</p>\n"
                elif element.tag == 'latex':
                    # Convert LaTeX to an image and embed it
                    img_tag = self.render_latex_to_image(element.text.strip())
                    content += f"<p>{img_tag}</p>\n"
                elif element.tag == 'python':  # Handle the <python> tag
                    src_file = element.get('src')
                    cache_enabled = element.get('cache', 'True').lower() == 'true'  # Default to True if not specified
                    if src_file:
                        content += self.execute_code_from_file(src_file, cache_enabled)  # Execute Python code from file
                    else:
                        content += "Error: No source file specified.\n"
                elif element.tag == 'link':
                    content += f"<a href='{element.get('href')}'>{element.text}</a>\n"
                # Add more handlers for other elements as needed...

            # Close HTML content
            content += """
            </body>
            </html>
            """

            # Load the HTML content into the web view with a base URL
            base_url = QUrl.fromLocalFile(os.path.dirname(os.path.realpath(__file__)) + '/')
            self.web_view.setHtml(content, base_url)
        except Exception as e:
            self.web_view.setHtml(f"<p>Error parsing PyML: {e}</p>")

    def handle_link_click(self, url):
        # Convert the URL to a local file path
        pyml_file = url.toLocalFile()

        # Print the path for debugging
        print(f"Resolved file path: {pyml_file}")

        # Check if the file is a valid .pyml file and exists
        if pyml_file.endswith('.pyml') and os.path.exists(pyml_file):
            self.load_pyml_file(pyml_file)
        else:
            print(f"Error: File {pyml_file} does not exist.")


    def render_latex_to_image(self, latex_code):
        try:
            # Ensure the "tmp" directory exists and has correct permissions
            output_dir = ensure_tmp_directory()

            # Check if LaTeX and dvipng are installed
            if not shutil.which("latex") or not shutil.which("dvipng"):
                raise EnvironmentError("LaTeX or dvipng program is not installed or not found in PATH.")

            # Create a hash of the LaTeX code
            latex_hash = hashlib.md5(latex_code.encode('utf-8')).hexdigest()
            output_image_path = os.path.join(output_dir, f"{latex_hash}.png")

            # Check if the image already exists
            if not os.path.exists(output_image_path):
                # Render the LaTeX code to a PNG image
                result = preview(latex_code, viewer='file', filename=output_image_path, dvioptions=["-D", "150"])
                if result is not None:
                    raise RuntimeError(f"dvipng error: {result}")

            # Return an HTML img tag with the relative path to the generated image
            return f'<img src="{output_image_path}" alt="LaTeX Image">'
        except EnvironmentError as e:
            return f"<p>Error rendering LaTeX: {e}</p>\n"
        except RuntimeError as e:
            return f"<p>Error rendering LaTeX: {e}</p>\n"
        except Exception as e:
            return f"<p>Error rendering LaTeX: {e}</p>\n"

    def resolve_relative_path(self, path):
        # If the path is relative, convert it to an absolute URL using the base URL
        if self.base_url and not urlparse(path).scheme:
            return urljoin(self.base_url, path)
        return path

    def execute_code_from_file(self, file_path, cache_enabled=True):
        try:
            # Resolve the path to make it an absolute URL if needed
            file_path = self.resolve_relative_path(file_path)

            # Determine if the file path is local or remote
            is_remote = file_path.startswith('http')

            # Read the Python script content
            if is_remote:
                # Load script from the remote URL
                response = requests.get(file_path)
                response.raise_for_status()
                code = response.text
            else:
                # Load script from the local file
                with open(file_path, 'r') as file:
                    code = file.read()

            # Generate a hash for the script content
            script_hash = hashlib.md5(code.encode('utf-8')).hexdigest()
            cached_output_html = f"tmp/{script_hash}.html"
            cached_output_img = f"tmp/{script_hash}.png"

            # Check if caching is enabled and the cached output exists
            if cache_enabled:
                if os.path.exists(cached_output_html):
                    # Return the cached HTML content if it exists
                    return f'<iframe src="{cached_output_html}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>'
                elif os.path.exists(cached_output_img):
                    # Return the cached image if it exists
                    return f'<img src="{cached_output_img}" alt="Python Output Image" />'

            # Execute the script and capture the output
            exec_locals = {}
            exec(code, {}, exec_locals)
            output = exec_locals.get("output", "")

            # Determine the type of output (image or HTML)
            if output.endswith('.png'):
                # Cache the image output if caching is enabled
                if cache_enabled:
                    os.rename(output, cached_output_img)
                return f'<img src="{cached_output_img if cache_enabled else output}" alt="Python Output Image" />'
            elif output.endswith('.html'):
                # Cache the HTML output if caching is enabled
                if cache_enabled:
                    os.rename(output, cached_output_html)
                return f'<iframe src="{cached_output_html if cache_enabled else output}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>'
            else:
                # Default to displaying raw output
                return f"<pre>{output}</pre>\n"
        except Exception as e:
            return f"Error executing code from file: {e}\n"



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyMLRenderer()
    window.show()
    sys.exit(app.exec())
