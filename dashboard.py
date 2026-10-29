from __future__ import annotations
import io
from typing import Optional
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, clear_output, display

class CsvStatisticsDashboard:
    """Dashboard phân tích CSV bằng ipywidgets và Voilà."""
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
    MAX_ROWS = 300_000
    MAX_COLUMNS = 200

    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.file_name: Optional[str] = None
        self._create_widgets()
        self._register_callbacks()
        self._set_data_controls(False)

    def _create_widgets(self) -> None:
        self.title = widgets.HTML("""
        <div style="padding: 18px 22px; border-radius: 14px;
        background: linear-gradient(135deg, #0b5cab, #338eda);
        color:white; margin-bottom: 16px">
        <h2 style="margin: 0 0 6px 0">Phân tích thống kê dữ liệu CSV</h2>
        <div>Upload dữ liệu, chọn biến, tính thống kê và trực quan hóa.</div>
        </div>""")

        self.upload = widgets.FileUpload(
            accept=".csv, text/csv", multiple=False,
            description="Chọn CSV", button_style="primary", icon="upload"
        )
        self.separator = widgets.Dropdown(
            options=[("Tự động", "auto"), ("Dấu phẩy", ","),
                     ("Dấu chấm phẩy", ";"), ("Tab", "\t"),
                     ("Gạch đứng", "|")],
            value="auto", description="Phân cách:"
        )
        self.decimal = widgets.Dropdown(
            options=[("Dấu chấm", "."), ("Dấu phẩy", ",")],
            value=".", description="Thập phân:"
        )
        self.reload_button = widgets.Button(
            description="Đọc lại", icon="refresh", button_style="info"
        )
        self.status = widgets.HTML("<b>Chưa có dữ liệu.</b>")
        self.numeric_only = widgets.Checkbox(
            value=False, description="Chỉ hiện cột số", indent=False
        )
        self.column_selector = widgets.SelectMultiple(
            options=[], description="Cột:", rows=8,
            layout=widgets.Layout(width="100%")
        )
        self.table_size = widgets.Dropdown(
            options=[5, 10, 20, 50, 100], value=10, description="Số dòng:"
        )
        self.show_index = widgets.Checkbox(
            value=False, description="Hiện chỉ số", indent=False
        )
        self.show_table_button = widgets.Button(
            description="Hiện bảng", icon="table", button_style="primary"
        )
        self.statistic_selector = widgets.SelectMultiple(
            options=[("Số hợp lệ", "count"), ("Số thiếu", "missing"),
                     ("Trung bình", "mean"), ("Độ lệch chuẩn", "std"),
                     ("Nhỏ nhất", "min"), ("Q1", "q1"),
                     ("Trung vị", "median"), ("Q3", "q3"),
                     ("Lớn nhất", "max"), ("Số giá trị khác nhau", "nunique")],
            value=("count", "missing", "mean", "std", "min", "median", "max"),
            description="Thống kê:", rows=10,
            layout=widgets.Layout(width="100%")
        )
        self.calculate_button = widgets.Button(
            description="Tính thống kê", icon="calculator", button_style="success"
        )
        self.chart_type = widgets.Dropdown(
            options=[("Histogram", "hist"), ("Boxplot", "box"),
                     ("Scatter", "scatter"), ("Đường", "line"),
                     ("Cột", "bar")],
            value="hist", description="Biểu đồ:"
        )
        self.x_column = widgets.Dropdown(options=[], description="Trục X:")
        self.y_column = widgets.Dropdown(options=[], description="Trục Y:")
        self.bins = widgets.IntSlider(
            value=20, min=5, max=100, step=5, description="Số lớp:",
            continuous_update=False
        )
        self.figure_width = widgets.FloatSlider(
            value=9, min=5, max=16, step=0.5, description="Rộng:",
            continuous_update=False
        )
        self.figure_height = widgets.FloatSlider(
            value=5, min=3, max=10, step=0.5, description="Cao:",
            continuous_update=False
        )
        self.plot_button = widgets.Button(
            description="Vẽ biểu đồ", icon="bar-chart", button_style="warning"
        )

        self.summary_output = widgets.Output()
        self.table_output = widgets.Output()
        self.statistics_output = widgets.Output()
        self.chart_output = widgets.Output()

        upload_box = widgets.VBox([
            widgets.HTML("<h3>1. Upload dữ liệu</h3>"),
            widgets.HBox([self.upload, self.reload_button]),
            widgets.HBox([self.separator, self.decimal]),
            self.status, self.summary_output
        ])
        table_box = widgets.VBox([
            widgets.HTML("<h3>2. Chọn biến và xem dữ liệu</h3>"),
            self.numeric_only, self.column_selector,
            widgets.HBox([self.table_size, self.show_index, self.show_table_button]),
            self.table_output
        ])
        stat_box = widgets.VBox([
            widgets.HTML("<h3>3. Thống kê mô tả</h3>"),
            self.statistic_selector, self.calculate_button,
            self.statistics_output
        ])
        chart_box = widgets.VBox([
            widgets.HTML("<h3>4. Vẽ biểu đồ</h3>"),
            self.chart_type, widgets.HBox([self.x_column, self.y_column]),
            self.bins, self.figure_width, self.figure_height,
            self.plot_button, self.chart_output
        ])

        accordion = widgets.Accordion(
            children=[upload_box, table_box, stat_box, chart_box],
            selected_index=0
        )
        for index, name in enumerate(["Upload CSV", "Bảng dữ liệu", "Thống kê", "Biểu đồ"]):
            accordion.set_title(index, name)

        self.root = widgets.VBox(
            [self.title, accordion, widgets.HTML("<small>Dữ liệu chỉ tồn tại trong phiên hiện tại.</small>")],
            layout=widgets.Layout(width="100%", max_width="1200px", margin="0 auto")
        )

    def _register_callbacks(self) -> None:
        self.upload.observe(self._on_upload, names="value")
        self.reload_button.on_click(self._on_reload)
        self.numeric_only.observe(self._on_numeric_filter, names="value")
        self.show_table_button.on_click(self._show_table)
        self.calculate_button.on_click(self._calculate_statistics)
        self.plot_button.on_click(self._draw_chart)
        self.chart_type.observe(self._update_chart_controls, names="value")

    def _data_controls(self):
        return [self.column_selector, self.numeric_only, self.table_size,
                self.show_index, self.show_table_button,
                self.statistic_selector, self.calculate_button,
                self.chart_type, self.x_column, self.y_column, self.bins,
                self.figure_width, self.figure_height, self.plot_button]

    def _set_data_controls(self, enabled: bool) -> None:
        for control in self._data_controls():
            control.disabled = not enabled
        self.reload_button.disabled = not bool(self.upload.value)

    @staticmethod
    def _extract_uploaded_file(upload_value):
        if not upload_value:
            return None, None
        if isinstance(upload_value, dict):
            name = next(iter(upload_value))
            info = upload_value[name]
            return name, bytes(info["content"])
        info = upload_value[0]
        return info.get("name", "uploaded.csv"), bytes(info["content"])

    @staticmethod
    def _read_csv_bytes(content: bytes, separator: str, decimal: str):
        errors = []
        for encoding in ["utf-8-sig", "utf-8", "cp1258", "latin1"]:
            try:
                options = dict(encoding=encoding, decimal=decimal)
                if separator == "auto":
                    options.update(sep=None, engine="python")
                else:
                    options.update(sep=separator)
                return pd.read_csv(io.BytesIO(content), **options)
            except (UnicodeDecodeError, pd.errors.ParserError) as error:
                errors.append(error)
        raise ValueError("Không đọc được CSV; kiểm tra mã hóa và dấu phân cách.")

    def _on_upload(self, change) -> None:
        self._load_uploaded_file()

    def _on_reload(self, button) -> None:
        self._load_uploaded_file()

    def _load_uploaded_file(self) -> None:
        name, content = self._extract_uploaded_file(self.upload.value)
        self.reload_button.disabled = content is None
        if content is None:
            return
        if len(content) > self.MAX_FILE_SIZE:
            self._show_error("File vượt giới hạn 15 MB.")
            return
        try:
            df = self._read_csv_bytes(content, self.separator.value, self.decimal.value)
        except Exception as error:
            self._show_error(str(error))
            return
        if df.empty:
            self._show_error("File không chứa dữ liệu.")
            return
        if len(df) > self.MAX_ROWS:
            self._show_error(f"File vượt giới hạn {self.MAX_ROWS:,} dòng.")
            return
        if df.shape[1] > self.MAX_COLUMNS:
            self._show_error(f"File vượt giới hạn {self.MAX_COLUMNS} cột.")
            return

        self.df, self.file_name = df, name
        self.status.value = (
            f"<span style='color:#137333'><b>Đã đọc: </b>"
            f"{name} | {df.shape[0]:,} dòng | {df.shape[1]:,} cột</span>"
        )
        self._set_data_controls(True)
        self._refresh_column_controls()
        self._show_data_summary()

    def _show_error(self, message: str) -> None:
        self.df = None
        self.status.value = f"<span style='color:#b00020'><b>Lỗi:</b> {message}</span>"
        self._set_data_controls(False)

    def _refresh_column_controls(self) -> None:
        if self.df is None:
            return
        all_columns = list(self.df.columns)
        numeric_columns = list(self.df.select_dtypes(include=np.number).columns)
        shown = numeric_columns if self.numeric_only.value else all_columns
        self.column_selector.options = shown
        self.column_selector.value = tuple(shown[:5])
        self.x_column.options = all_columns
        self.y_column.options = numeric_columns or all_columns
        if all_columns:
            self.x_column.value = all_columns[0]
        if self.y_column.options:
            self.y_column.value = self.y_column.options[0]
        self._update_chart_controls()

    def _on_numeric_filter(self, change) -> None:
        self._refresh_column_controls()

    def _show_data_summary(self) -> None:
        summary = pd.DataFrame({
            "Kiểu dữ liệu": self.df.dtypes.astype(str),
            "Hợp lệ": self.df.notna().sum(),
            "Thiếu": self.df.isna().sum(),
            "Phân biệt": self.df.nunique(dropna=True),
        })
        with self.summary_output:
            clear_output(wait=True)
            display(HTML("<h4>Tóm tắt cấu trúc dữ liệu</h4>"))
            display(summary)

    def _selected_columns(self):
        if self.df is None:
            return []
        return list(self.column_selector.value) or list(self.df.columns)

    def _show_table(self, button) -> None:
        if self.df is None:
            return
        table = self.df.loc[:, self._selected_columns()].head(self.table_size.value)
        with self.table_output:
            clear_output(wait=True)
            display(HTML(f"<h4>{len(table)} dòng đầu tiên</h4>"))
            if self.show_index.value:
                display(table)
            else:
                display(HTML(table.to_html(index=False, escape=True)))

    @staticmethod
    def _column_statistic(series: pd.Series, statistic: str):
        if statistic == "count":
            return series.count()
        if statistic == "missing":
            return series.isna().sum()
        if statistic == "nunique":
            return series.nunique(dropna=True)
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() == 0:
            return np.nan
        functions = {
            "mean": numeric.mean, "std": numeric.std, "min": numeric.min,
            "q1": lambda: numeric.quantile(0.25),
            "q3": lambda: numeric.quantile(0.75),
            "median": numeric.median, "max": numeric.max,
        }
        return functions[statistic]()

    def _calculate_statistics(self, button) -> None:
        if self.df is None:
            return
        statistics = list(self.statistic_selector.value)
        if not statistics:
            with self.statistics_output:
                clear_output(wait=True)
                print("Hãy chọn ít nhất một thống kê.")
            return
        labels = {value: label for label, value in self.statistic_selector.options}
        columns = self._selected_columns()
        result = pd.DataFrame(index=columns)
        for statistic in statistics:
            result[labels[statistic]] = [
                self._column_statistic(self.df[column], statistic) for column in columns
            ]
        result.index.name = "Biến"
        with self.statistics_output:
            clear_output(wait=True)
            display(HTML("<h4>Kết quả thống kê</h4>"))
            display(result.round(4))

    def _update_chart_controls(self, change=None) -> None:
        chart = self.chart_type.value
        self.bins.layout.display = "" if chart == "hist" else "none"
        self.x_column.disabled = chart in {"hist", "box"}

    def _numeric_values(self, column):
        return pd.to_numeric(self.df[column], errors="coerce").dropna()

    def _draw_chart(self, button) -> None:
        if self.df is None:
            return
        chart, x_col, y_col = (
            self.chart_type.value, self.x_column.value, self.y_column.value
        )
        with self.chart_output:
            clear_output(wait=True)
            try:
                fig, ax = plt.subplots(figsize=(self.figure_width.value, self.figure_height.value))
                if chart == "hist":
                    ax.hist(self._numeric_values(y_col), bins=self.bins.value, edgecolor="black", alpha=0.75)
                    ax.set(xlabel=y_col, ylabel="Tần số", title=f"Histogram của {y_col}")
                elif chart == "box":
                    ax.boxplot(self._numeric_values(y_col), tick_labels=[y_col])
                    ax.set(ylabel="Giá trị", title=f"Boxplot của {y_col}")
                elif chart in {"scatter", "line"}:
                    data = self.df[[x_col, y_col]].copy()
                    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
                    data = data.dropna()
                    if chart == "scatter":
                        ax.scatter(data[x_col], data[y_col], alpha=0.7)
                    else:
                        ax.plot(data[x_col], data[y_col], marker="o", markersize=3)
                    ax.set(xlabel=x_col, ylabel=y_col, title=f"{y_col} theo {x_col}")
                else:  # bar
                    data = self.df[[x_col, y_col]].copy()
                    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
                    grouped = data.dropna().groupby(x_col)[y_col].mean().head(30)
                    grouped.plot(kind="bar", ax=ax, color="#338eda")
                    ax.set(xlabel=x_col, ylabel=f"Trung bình {y_col}", title=f"Trung bình {y_col} theo {x_col}")
                
                ax.grid(alpha=0.2)
                plt.tight_layout()
                plt.show()
            except Exception as error:
                plt.close("all")
                print(f"Không thể vẽ biểu đồ: {error}")

    def display(self) -> None:
        display(self.root)

def create_app() -> CsvStatisticsDashboard:
    app = CsvStatisticsDashboard()
    app.display()
    return app