import sys
import os
import hashlib
import requests
import shutil
import stat
import textwrap
from urllib.parse import urlparse, urljoin, unquote
from sympy import preview  # For rendering LaTeX equations as images
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
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

def convert_file_url_to_local_path(file_url):
    # Convert 'file://' URL to local path
    if file_url.startswith('file://'):
        # Remove 'file://' prefix and unquote to handle spaces or special characters
        return unquote(file_url[7:])
    return file_url

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, renderer):
        super().__init__()
        self.renderer = renderer

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        url_str = url.toString()
        # If the URL is a .pyml file, handle it manually
        if url_str.endswith('.pyml'):
            self.renderer.load_pyml_file(url_str)
            return False  # Prevent default navigation
        # Allow normal navigation for other URLs
        return True

class PyMLRenderer(QMainWindow):
    def __init__(self, enable_javascript=True):
        super().__init__()

        self.root_base_url = None  # Store the root base URL
        self.current_base_url = None  # Store the current base URL for relative links
        self.initial_load = True  # Flag to prevent recursive handling
        self.handling_link = False  # Flag to prevent recursive handling
        self.enable_javascript = enable_javascript

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

        # Create a horizontal layout for the URL bar
        url_layout = QHBoxLayout()

        # URL bar (QLineEdit)
        self.url_bar = QLineEdit(self)
        self.url_bar.setPlaceholderText("Enter file path or URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)  # Trigger navigation when Enter is pressed
        url_layout.addWidget(self.url_bar)

        # "Go" button
        go_button = QPushButton("Go", self)
        go_button.clicked.connect(self.navigate_to_url)  # Trigger navigation when the button is clicked
        url_layout.addWidget(go_button)

        # Add the URL layout to the main layout
        layout.addLayout(url_layout)

        # Web view for displaying content
        self.web_view = QWebEngineView()
        self.web_page = CustomWebEnginePage(self)
        self.web_view.setPage(self.web_page)
        # self.web_view.urlChanged.connect(self.handle_link_click)
        # self.web_view.urlChanged.connect(self.update_url_bar)  # Connect URL change to update method
        layout.addWidget(self.web_view)

        # Central widget setup
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Apply initial JavaScript setting
        self.apply_javascript_setting()

        # Load initial PyML content from a file
        # self.load_pyml_file("https://raw.githubusercontent.com/RadEZorack/Galacton/main/index.pyml")
        # self.load_pyml_file("index.pyml")
        # Set initial content URL
        initial_url = "https://raw.githubusercontent.com/RadEZorack/Galacton/main/index.pyml"
        # initial_url = "index.pyml"
        # self.url_bar.setText(initial_url)  # Set the initial URL in the URL bar
        self.load_pyml_file(initial_url)

    def navigate_to_url(self):
        # Get the URL from the URL bar
        url = self.url_bar.text()

        # Call the load_pyml_file function to navigate to the entered URL
        self.load_pyml_file(url)

    # def update_url_bar(self, url):
    #     # Update the URL bar with the current URL
    #     print(url.toString())
    #     self.url_bar.setText(url.toString())

    def apply_javascript_setting(self):
        # Use QWebEngineSettings to enable or disable JavaScript
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, self.enable_javascript)

    def toggle_javascript(self):
        # Update JavaScript setting based on checkbox
        self.enable_javascript = self.javascript_checkbox.isChecked()
        self.apply_javascript_setting()

    def load_pyml_file(self, file_path):
        try:
            # Convert file URL to a local path if necessary
            if file_path.startswith('file://'):
                file_path = convert_file_url_to_local_path(file_path)

            # Update the URL bar with the current URL
            self.url_bar.setText(file_path)
                
            # Check if the path is a URL
            parsed_url = urlparse(file_path)
            if parsed_url.scheme in ['http', 'https']:
                # Fetch content from the URL
                response = requests.get(file_path)
                response.raise_for_status()  # Check for HTTP errors
                pyml_content = response.text
                
                # Store the root base URL if not already set
                if not self.root_base_url:
                    self.root_base_url = os.path.dirname(file_path) + '/'

                # Update the current base URL to the directory of the current file
                self.current_base_url = os.path.dirname(file_path) + '/'

            else:
                # Load content from a local file
                with open(file_path, 'r') as file:
                    pyml_content = file.read()
                    self.current_base_url = os.path.dirname(os.path.abspath(file_path)) + '/'  # Store local base path


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
                attrs = ' '.join(f'{key}="{value}"' for key, value in element.attrib.items())
                if element.tag == 'meta':
                    # parse the meta tag if needed. But don't include in final output
                    pass
                elif element.tag == 'latex':
                    # Convert LaTeX to an image and embed it
                    img_tag = self.render_latex_to_image(element.text.strip())
                    content += f"<div {attrs}>{img_tag}</div>\n"
                elif element.tag == 'python':  # Handle the <python> tag
                    src_file = element.get('src')
                    cache_enabled = element.get('cache', 'True').lower() == 'true'

                    # Use the new unified function to handle both inline code and source files
                    content += self.execute_python_code(element.text, src_file, cache_enabled)

                elif element.tag == 'a':
                    # Resolve relative URLs
                    href = self.resolve_relative_path(element.get('href'))
                    content += f"<a href='{href}'>{element.text}</a>\n"
                else:
                    # Handle all other tags generically, including their attributes
                    content += f"<{element.tag} {attrs}>{element.text or ''}</{element.tag}>\n"
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

    # def handle_link_click(self, url):
    #     # Only handle the link if it's not the initial page load
    #     if self.initial_load:
    #         self.initial_load = False
    #         return
        
    #     # Avoid recursive handling
    #     if self.handling_link:
    #         return

    #     # Start handling the link
    #     self.handling_link = True
    #     url_str = url.toString()
    #     print(f"url_str {url_str}")

    #     if url_str.endswith('.pyml'):
    #         self.load_pyml_file(url_str)
    #     else:
    #         # For other links, navigate normally
    #         self.web_view.setUrl(url)

    #     # End handling the link
    #     self.handling_link = False


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
        # If the path is already a complete URL, return it as is
        if urlparse(path).scheme in ['http', 'https']:
            return path

        # If working with a remote base URL
        # if self.root_base_url and self.root_base_url.startswith('http'):
        #     return urljoin(self.root_base_url, path)
        # Use the correct base URL (remote or local)
        if self.current_base_url.startswith('http'):
            # If currently using a remote base URL, use urljoin for proper resolution
            return urljoin(self.current_base_url, path)

        # Otherwise, assume it's a local file path
        return os.path.abspath(os.path.join(self.current_base_url, path))


    def execute_python_code(self, inline_code=None, src_file=None, cache_enabled=True):
        try:
            # Determine if we're executing inline code or loading from a file
            if src_file:
                # Resolve the path to make it an absolute URL if needed
                file_path = self.resolve_relative_path(src_file)

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

            else:
                # Use inline code directly, dedenting to handle any leading spaces
                code = textwrap.dedent(inline_code or "")

            # Generate a hash for the script content
            script_hash = hashlib.md5(code.encode('utf-8')).hexdigest()
            cached_output_html = f"tmp/{script_hash}.html"
            cached_output_img = f"tmp/{script_hash}.png"

            # Check if caching is enabled and the cached output exists
            if cache_enabled:
                if os.path.exists(cached_output_html):
                    return f'<iframe src="{cached_output_html}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>'
                elif os.path.exists(cached_output_img):
                    return f'<img src="{cached_output_img}" alt="Python Output Image" />'

            # Execute the script and capture the output
            exec_locals = {}
            exec(code, {}, exec_locals)
            output = exec_locals.get("output", "")

            # Determine the type of output (image or HTML)
            if isinstance(output, str):
                if output.endswith('.png'):
                    if cache_enabled:
                        os.rename(output, cached_output_img)
                    return f'<img src="{cached_output_img if cache_enabled else output}" alt="Python Output Image" />'
                elif output.endswith('.html'):
                    if cache_enabled:
                        os.rename(output, cached_output_html)
                    return f'<iframe src="{cached_output_html if cache_enabled else output}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>'
            # Default to displaying raw output if it's not a recognized file type
            return f"<pre>{output}</pre>\n"
        except Exception as e:
            return f"Error executing code: {e}\n"



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyMLRenderer()
    window.show()
    sys.exit(app.exec())
