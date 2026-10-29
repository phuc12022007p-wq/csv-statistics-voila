from pathlib import Path
import nbformat as nbf

def build_notebook() -> None:
    notebook = nbf.v4.new_notebook()
    notebook["cells"] = [
        nbf.v4.new_markdown_cell(
            "# Ứng dụng phân tích thống kê CSV\n"
            "Upload CSV, chọn biến, tính thống kê và vẽ biểu đồ."
        ),
        nbf.v4.new_code_cell(
            "from dashboard import create_app\n\n"
            "app = create_app()"
        ),
    ]
    notebook["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3"},
    }
    output_path = Path("app.ipynb")
    with output_path.open("w", encoding="utf-8") as stream:
        nbf.write(notebook, stream)
    print(f"Đã tạo notebook: {output_path.resolve()}")

if __name__ == "__main__":
    build_notebook()