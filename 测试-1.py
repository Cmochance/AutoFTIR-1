from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _bootstrap_runtime() -> Path:
	base_dir = Path(__file__).resolve().parent
	os.environ["FTIR_PICTURE_BASE_DIR"] = str(base_dir)
	os.chdir(base_dir)
	return base_dir


def _require_dependencies() -> None:
	missing: list[str] = []
	try:
		import pandas  # noqa: F401
	except Exception:
		missing.append("pandas")
	try:
		import matplotlib  # noqa: F401
	except Exception:
		missing.append("matplotlib")

	if missing:
		print("缺少依赖，无法运行。请先安装：")
		print("  " + " ".join(missing))
		print("\n建议在项目目录执行：")
		print("  pip install -r requirements.txt")
		input("\n按回车键退出...")
		raise SystemExit(1)


BASE_DIR = _bootstrap_runtime()
_require_dependencies()


import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# 1. 设置全局风格
plt.style.use('default')
plt.rcParams['font.family'] = 'Arial'  # 科研常用字体
plt.rcParams['font.size'] = 12

def main() -> None:
	# 2. 读取数据（.txt：两列数字，多个空格/空白分隔，无表头）
	# 注意：脚本会自动切换到自身所在目录运行
	data_path = BASE_DIR / "测试-1.txt"
	if not data_path.exists():
		print(f"未找到数据文件：{data_path}")
		input("\n按回车键退出...")
		raise SystemExit(1)

	df = pd.read_csv(data_path, sep=r"\s+", engine="python", header=None, usecols=[0, 1])
	x = df.iloc[:, 0]
	y = df.iloc[:, 1]

	# 3. 创建画布
	fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)

	# 4. 绘图
	ax.plot(x, y, color="#1f77b4", linewidth=1.5, label="测试-1.txt")

	# 5. 细节调整
	ax.set_xlabel(r"2$\theta$ (degree)", fontsize=14, fontweight="bold")
	ax.set_ylabel(r"Intensity (a.u.)", fontsize=14, fontweight="bold")
	ax.tick_params(direction="in", length=6, width=1)

	# 去除上方和右方边框
	ax.spines["top"].set_visible(False)
	ax.spines["right"].set_visible(False)
	ax.spines["left"].set_linewidth(1.2)
	ax.spines["bottom"].set_linewidth(1.2)

	plt.legend(frameon=False)
	plt.tight_layout()

	# 6. 保存
	output_path = BASE_DIR / "测试-1_plot.png"
	plt.savefig(output_path)
	print(f"图片已保存为: {output_path}")
	plt.show()


if __name__ == "__main__":
	try:
		main()
	except SystemExit:
		raise
	except Exception:  # noqa: BLE001
		print("运行出错：")
		traceback.print_exc()
		input("\n按回车键退出...")
