# Galacton

Galacton is a specialized web-like browser designed for academics and researchers. It provides a clean, distraction-free environment for exploring complex ideas, interacting with dynamic content, and sharing knowledge in a way that's more focused than the traditional web.

## Features

- Render LaTeX math equations and Python code dynamically.
- Navigate between documents using a custom `.pyml` format.
- Integrated environment for learning, teaching, and research.

## Getting Started

### Prerequisites

Make sure you have Python 3.x installed. You’ll also need a LaTeX distribution (like TeX Live or MacTeX) for rendering LaTeX equations.

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/RadEZorack/galacton.git
    cd galacton
    ```

2. Set up a virtual environment and install dependencies:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip3 install -r requirements.txt
    ```

3. Run the application:
    ```bash
    python3 main.py
    ```

### Usage

- Open and navigate between `.pyml` documents.
- Interact with LaTeX and Python code blocks directly.

### Linking Between Files

When creating links between `.pyml` files, use the file name directly without preceding relative paths (e.g., `index.pyml` instead of `../index.pyml`). The Galacton renderer automatically handles these links within the context of the current directory.

### Contributing

Feel free to fork this repository and submit pull requests. Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python, PyQt5, and SymPy.
- Inspired by the need for a distraction-free academic browser.
