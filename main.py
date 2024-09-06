import sys
import os
import hashlib
from sympy import preview  # For rendering LaTeX equations as images
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from lxml import etree  # For parsing XML-like syntax

class PyMLRenderer(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.load_pyml_file("index.pyml")

    def load_pyml_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                pyml_content = file.read()
            self.parse_pyml(pyml_content)
        except Exception as e:
            self.web_view.setHtml(f"<p>Error loading PyML file: {e}</p>")

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
            # Define the output directory for temporary images
            output_dir = "tmp"
            os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Create a hash of the LaTeX code
            latex_hash = hashlib.md5(latex_code.encode('utf-8')).hexdigest()

            # Define the output image path using the hash
            output_image_path = os.path.join(output_dir, f"{latex_hash}.png")

            # Check if the image already exists
            if not os.path.exists(output_image_path):
                # Render the LaTeX code to a PNG image
                preview(latex_code, viewer='file', filename=output_image_path, dvioptions=["-D", "150"])

            # Return an HTML img tag with the relative path to the generated image
            return f'<img src="{output_image_path}" alt="LaTeX Image">'
        except Exception as e:
            return f"Error rendering LaTeX: {e}\n"

    def execute_code_from_file(self, file_path, cache_enabled=True):
        try:
            # Read the Python script content
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
