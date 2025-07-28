import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.optimize import curve_fit
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 配置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class DataVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("数据可视化与预测系统")
        self.root.geometry("1200x800")
        
        # 数据存储
        self.data = None
        self.fitted_func = None
        self.fitted_params = None
        self.r_squared = 0
        
        # 创建界面
        self.create_widgets()
        
        # 加载数据
        self.load_data()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 数据信息
        info_frame = ttk.LabelFrame(control_frame, text="数据信息")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="正在加载数据...")
        self.info_label.pack(padx=10, pady=10)
        
        # 拟合选项
        fit_frame = ttk.LabelFrame(control_frame, text="函数拟合")
        fit_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.fit_type = tk.StringVar(value="exponential_decay")
        ttk.Radiobutton(fit_frame, text="指数衰减 (y=ae^(-λt))", variable=self.fit_type, 
                       value="exponential_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="线性衰减 (y=a-bt)", variable=self.fit_type, 
                       value="linear_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="多项式衰减 (y=at^(-n))", variable=self.fit_type, 
                       value="polynomial_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="高斯衰减", variable=self.fit_type, 
                       value="gaussian_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="对数衰减 (y=a-b*ln(t))", variable=self.fit_type, 
                       value="logarithmic_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="幂函数衰减 (y=a*(1-r)^t)", variable=self.fit_type, 
                       value="power_decay").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(fit_frame, text="多项式拟合", variable=self.fit_type, 
                       value="polynomial").pack(anchor=tk.W, padx=10, pady=2)
        
        # 多项式阶数选择
        degree_frame = ttk.Frame(fit_frame)
        degree_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(degree_frame, text="多项式阶数:").pack(side=tk.LEFT)
        self.degree_var = tk.IntVar(value=3)
        degree_spin = ttk.Spinbox(degree_frame, from_=1, to=6, width=5, 
                                 textvariable=self.degree_var)
        degree_spin.pack(side=tk.RIGHT)
        
        ttk.Button(fit_frame, text="执行拟合", command=self.fit_function).pack(
            fill=tk.X, padx=10, pady=10)
        
        # 拟合结果
        result_frame = ttk.LabelFrame(control_frame, text="拟合结果")
        result_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.result_text = tk.Text(result_frame, height=10, width=30)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        self.result_text.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 预测功能
        predict_frame = ttk.LabelFrame(control_frame, text="数字预测")
        predict_frame.pack(fill=tk.X)
        
        ttk.Label(predict_frame, text="输入时间 (YYYY-MM-DD HH:MM:SS):").pack(
            padx=10, pady=(10, 5))
        
        self.time_entry = ttk.Entry(predict_frame, width=25)
        self.time_entry.pack(padx=10, pady=5)
        self.time_entry.insert(0, "2025-07-28 12:00:00")
        
        ttk.Button(predict_frame, text="预测数字", command=self.predict_value).pack(
            fill=tk.X, padx=10, pady=10)
        
        self.predict_label = ttk.Label(predict_frame, text="", foreground="blue")
        self.predict_label.pack(padx=10, pady=(0, 10))
        
        # 右侧图表区域
        chart_frame = ttk.Frame(main_frame)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建matplotlib图表
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 图表工具栏
        toolbar_frame = ttk.Frame(chart_frame)
        toolbar_frame.pack(fill=tk.X)
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
    def load_data(self):
        """加载数据文件"""
        try:
            # 读取数据
            data = []
            with open('filtered_comments.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) == 2:
                            time_str, value_str = parts
                            timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                            value = float(value_str)
                            data.append((timestamp, value))
            
            # 转换为DataFrame
            self.data = pd.DataFrame(data, columns=['time', 'value'])
            self.data = self.data.sort_values('time')
            
            # 创建数值型时间轴（从第一个时间点开始的小时数）
            start_time = self.data['time'].iloc[0]
            self.data['hours'] = (self.data['time'] - start_time).dt.total_seconds() / 3600
            
            # 更新信息显示
            info_text = f"数据点数量: {len(self.data)}\n"
            info_text += f"时间范围: {self.data['time'].iloc[0].strftime('%Y-%m-%d %H:%M')}\n"
            info_text += f"至 {self.data['time'].iloc[-1].strftime('%Y-%m-%d %H:%M')}\n"
            info_text += f"数值范围: {self.data['value'].min():.1f} - {self.data['value'].max():.1f}"
            self.info_label.config(text=info_text)
            
            # 绘制原始数据
            self.plot_data()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
    
    def plot_data(self):
        """绘制数据图表"""
        self.ax.clear()
        
        # 绘制原始数据点
        self.ax.scatter(self.data['hours'], self.data['value'], 
                       alpha=0.6, s=20, color='blue', label='原始数据')
        
        # 如果有拟合函数，绘制拟合曲线
        if self.fitted_func is not None:
            x_smooth = np.linspace(self.data['hours'].min(), 
                                 self.data['hours'].max(), 1000)
            y_smooth = self.fitted_func(x_smooth, *self.fitted_params)
            self.ax.plot(x_smooth, y_smooth, 'r-', linewidth=2, label='拟合曲线')
        
        self.ax.set_xlabel('时间 (从开始时间的小时数)')
        self.ax.set_ylabel('数值')
        self.ax.set_title('数据可视化与函数拟合')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    # 衰减函数定义
    def exponential_decay_func(self, t, a, lam, c):
        """指数衰减函数: y = a * e^(-λt) + c"""
        return a * np.exp(-lam * t) + c
    
    def linear_decay_func(self, t, a, b):
        """线性衰减函数: y = a - bt"""
        return a - b * t
    
    def polynomial_decay_func(self, t, a, n, c):
        """多项式衰减函数: y = a * t^(-n) + c"""
        return a * np.power(t + 1, -n) + c  # +1避免t=0时的问题
    
    def gaussian_decay_func(self, t, a, mu, sigma, c):
        """高斯衰减函数: y = a * e^(-(t-μ)²/(2σ²)) + c"""
        return a * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2)) + c
    
    def logarithmic_decay_func(self, t, a, b):
        """对数衰减函数: y = a - b * ln(t+1)"""
        return a - b * np.log(t + 1)  # +1避免t=0时的问题
    
    def power_decay_func(self, t, a, r, c):
        """幂函数衰减: y = a * (1-r)^t + c"""
        return a * np.power(1 - r, t) + c
    
    def polynomial_func(self, x, *params):
        """多项式函数"""
        return sum(p * x**i for i, p in enumerate(params))
    
    def fit_function(self):
        """执行函数拟合"""
        if self.data is None:
            messagebox.showerror("错误", "请先加载数据")
            return
        
        try:
            x = self.data['hours'].values
            y = self.data['value'].values
            
            fit_type = self.fit_type.get()
            
            if fit_type == "exponential_decay":
                # 指数衰减拟合
                initial_guess = [y[0] - y[-1], 0.01, y[-1]]
                popt, _ = curve_fit(self.exponential_decay_func, x, y, 
                                  p0=initial_guess, maxfev=5000)
                self.fitted_params = popt
                self.fitted_func = self.exponential_decay_func
                y_pred = self.exponential_decay_func(x, *popt)
                
            elif fit_type == "linear_decay":
                # 线性衰减拟合
                popt, _ = curve_fit(self.linear_decay_func, x, y)
                self.fitted_params = popt
                self.fitted_func = self.linear_decay_func
                y_pred = self.linear_decay_func(x, *popt)
                
            elif fit_type == "polynomial_decay":
                # 多项式衰减拟合
                initial_guess = [1000, 0.5, y[-1]]
                popt, _ = curve_fit(self.polynomial_decay_func, x, y, 
                                  p0=initial_guess, maxfev=5000)
                self.fitted_params = popt
                self.fitted_func = self.polynomial_decay_func
                y_pred = self.polynomial_decay_func(x, *popt)
                
            elif fit_type == "gaussian_decay":
                # 高斯衰减拟合
                initial_guess = [y[0] - y[-1], x[0], np.std(x), y[-1]]
                popt, _ = curve_fit(self.gaussian_decay_func, x, y, 
                                  p0=initial_guess, maxfev=5000)
                self.fitted_params = popt
                self.fitted_func = self.gaussian_decay_func
                y_pred = self.gaussian_decay_func(x, *popt)
                
            elif fit_type == "logarithmic_decay":
                # 对数衰减拟合
                popt, _ = curve_fit(self.logarithmic_decay_func, x, y)
                self.fitted_params = popt
                self.fitted_func = self.logarithmic_decay_func
                y_pred = self.logarithmic_decay_func(x, *popt)
                
            elif fit_type == "power_decay":
                # 幂函数衰减拟合
                initial_guess = [y[0] - y[-1], 0.01, y[-1]]
                popt, _ = curve_fit(self.power_decay_func, x, y, 
                                  p0=initial_guess, maxfev=5000)
                self.fitted_params = popt
                self.fitted_func = self.power_decay_func
                y_pred = self.power_decay_func(x, *popt)
                
            elif fit_type == "polynomial":
                # 传统多项式拟合
                degree = self.degree_var.get()
                coeffs = np.polyfit(x, y, degree)
                self.fitted_params = coeffs
                self.fitted_func = lambda x, *params: np.polyval(params, x)
                y_pred = np.polyval(coeffs, x)
            
            # 计算R²
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            self.r_squared = 1 - (ss_res / ss_tot)
            
            # 显示拟合结果
            self.display_fit_results()
            
            # 重新绘制图表
            self.plot_data()
            
        except Exception as e:
            messagebox.showerror("错误", f"拟合失败: {str(e)}")
    
    def display_fit_results(self):
        """显示拟合结果"""
        self.result_text.delete(1.0, tk.END)
        
        fit_type = self.fit_type.get()
        result_text = f"拟合类型: {fit_type}\n"
        result_text += f"R² = {self.r_squared:.6f}\n\n"
        
        if fit_type == "exponential_decay":
            a, lam, c = self.fitted_params
            result_text += f"指数衰减函数:\ny = {a:.6f} * e^(-{lam:.6f} * t) + {c:.6f}\n\n"
            result_text += f"衰减常数 λ = {lam:.6f}\n"
            result_text += f"半衰期 = {np.log(2)/lam:.2f} 小时\n"
            
        elif fit_type == "linear_decay":
            a, b = self.fitted_params
            result_text += f"线性衰减函数:\ny = {a:.6f} - {b:.6f} * t\n\n"
            result_text += f"衰减速度 = {b:.6f} 单位/小时\n"
            
        elif fit_type == "polynomial_decay":
            a, n, c = self.fitted_params
            result_text += f"多项式衰减函数:\ny = {a:.6f} * t^(-{n:.6f}) + {c:.6f}\n\n"
            
        elif fit_type == "gaussian_decay":
            a, mu, sigma, c = self.fitted_params
            result_text += f"高斯衰减函数:\ny = {a:.6f} * e^(-((t-{mu:.6f})²/(2*{sigma:.6f}²))) + {c:.6f}\n\n"
            
        elif fit_type == "logarithmic_decay":
            a, b = self.fitted_params
            result_text += f"对数衰减函数:\ny = {a:.6f} - {b:.6f} * ln(t+1)\n\n"
            
        elif fit_type == "power_decay":
            a, r, c = self.fitted_params
            result_text += f"幂函数衰减:\ny = {a:.6f} * (1-{r:.6f})^t + {c:.6f}\n\n"
            result_text += f"衰减率 = {r*100:.2f}%\n"
            
        elif fit_type == "polynomial":
            result_text += "多项式系数:\n"
            for i, coeff in enumerate(self.fitted_params):
                result_text += f"x^{len(self.fitted_params)-1-i}: {coeff:.6f}\n"
        
        # 计算衰减速度（导数）
        if fit_type in ["exponential_decay", "linear_decay", "logarithmic_decay"]:
            result_text += "\n当前衰减速度分析:\n"
            current_time = self.data['hours'].iloc[-1]
            
            if fit_type == "exponential_decay":
                a, lam, c = self.fitted_params
                decay_rate = -a * lam * np.exp(-lam * current_time)
                result_text += f"当前时刻衰减速度: {decay_rate:.6f} 单位/小时\n"
                
            elif fit_type == "linear_decay":
                a, b = self.fitted_params
                result_text += f"恒定衰减速度: {-b:.6f} 单位/小时\n"
                
            elif fit_type == "logarithmic_decay":
                a, b = self.fitted_params
                decay_rate = -b / (current_time + 1)
                result_text += f"当前时刻衰减速度: {decay_rate:.6f} 单位/小时\n"
        
        self.result_text.insert(1.0, result_text)
    
    def predict_value(self):
        """预测数值"""
        if self.fitted_func is None:
            messagebox.showerror("错误", "请先执行函数拟合")
            return
        
        try:
            # 解析输入时间
            time_str = self.time_entry.get().strip()
            target_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            # 计算相对小时数
            start_time = self.data['time'].iloc[0]
            hours = (target_time - start_time).total_seconds() / 3600
            
            # 预测数值
            if self.fit_type.get() == "polynomial":
                predicted_value = np.polyval(self.fitted_params, hours)
            else:
                predicted_value = self.fitted_func(hours, *self.fitted_params)
            
            # 显示结果（单位为万）
            result_text = f"预测结果: {predicted_value:.2f}万"
            self.predict_label.config(text=result_text)
            
            # 在图表上标记预测点
            self.ax.scatter([hours], [predicted_value], color='red', s=100, 
                          marker='*', label=f'预测点 ({predicted_value:.2f}万)')
            self.ax.legend()
            self.canvas.draw()
            
        except ValueError as e:
            messagebox.showerror("错误", "时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式")
        except Exception as e:
            messagebox.showerror("错误", f"预测失败: {str(e)}")

def main():
    root = tk.Tk()
    app = DataVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()