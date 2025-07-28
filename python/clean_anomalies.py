import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def detect_and_remove_anomalies():
    """检测并移除异常数据点"""
    
    # 读取数据
    data = []
    with open('filtered_comments.txt', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    time_str, value_str = parts
                    timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    value = float(value_str)
                    data.append((line_num, timestamp, value, line.strip()))
    
    # 转换为DataFrame
    df = pd.DataFrame(data, columns=['line_num', 'time', 'value', 'original_line'])
    df = df.sort_values('time')
    
    print(f"原始数据点数量: {len(df)}")
    print(f"数值范围: {df['value'].min():.1f} - {df['value'].max():.1f}")
    
    # 检测异常值的方法
    anomalies = []
    
    # 1. 明显的异常值 (基于数值范围)
    # 正常范围应该在1800-2100之间，超出这个范围的都是异常
    range_anomalies = df[(df['value'] > 2200) | (df['value'] < 1800)]
    anomalies.extend(range_anomalies.index.tolist())
    
    # 2. 使用IQR方法检测异常值
    Q1 = df['value'].quantile(0.25)
    Q3 = df['value'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    iqr_anomalies = df[(df['value'] < lower_bound) | (df['value'] > upper_bound)]
    anomalies.extend(iqr_anomalies.index.tolist())
    
    # 3. 使用Z-score方法检测异常值
    z_scores = np.abs((df['value'] - df['value'].mean()) / df['value'].std())
    z_anomalies = df[z_scores > 3]
    anomalies.extend(z_anomalies.index.tolist())
    
    # 4. 检测时间序列中的突变点
    # 计算相邻点的差值
    df_sorted = df.sort_values('time').reset_index(drop=True)
    df_sorted['value_diff'] = df_sorted['value'].diff().abs()
    
    # 如果相邻点差值超过50，认为是异常
    jump_threshold = 50
    jump_anomalies = df_sorted[df_sorted['value_diff'] > jump_threshold]
    anomalies.extend(jump_anomalies.index.tolist())
    
    # 去重异常索引
    anomalies = list(set(anomalies))
    anomaly_df = df.iloc[anomalies].copy()
    
    print(f"\n检测到的异常数据点:")
    print("=" * 60)
    for _, row in anomaly_df.iterrows():
        print(f"行 {row['line_num']:4d}: {row['time'].strftime('%Y-%m-%d %H:%M:%S')} - {row['value']:8.1f}")
    
    # 显示异常值统计
    print(f"\n异常值统计:")
    print(f"- 范围异常 (>2200 或 <1800): {len(range_anomalies)} 个")
    print(f"- IQR异常 (<{lower_bound:.1f} 或 >{upper_bound:.1f}): {len(iqr_anomalies)} 个")
    print(f"- Z-score异常 (|z|>3): {len(z_anomalies)} 个")
    print(f"- 跳跃异常 (相邻差值>{jump_threshold}): {len(jump_anomalies)} 个")
    print(f"- 总异常数量: {len(anomalies)} 个")
    
    # 创建清理后的数据
    clean_df = df.drop(anomalies).copy()
    clean_df = clean_df.sort_values('time')
    
    print(f"\n清理后数据点数量: {len(clean_df)}")
    print(f"清理后数值范围: {clean_df['value'].min():.1f} - {clean_df['value'].max():.1f}")
    
    # 保存清理后的数据
    with open('filtered_comments_cleaned.txt', 'w', encoding='utf-8') as f:
        for _, row in clean_df.iterrows():
            f.write(f"{row['time'].strftime('%Y-%m-%d %H:%M:%S')}\t{row['value']}\n")
    
    # 保存异常数据记录
    with open('anomalies_removed.txt', 'w', encoding='utf-8') as f:
        f.write("移除的异常数据点:\n")
        f.write("=" * 60 + "\n")
        for _, row in anomaly_df.iterrows():
            f.write(f"行 {row['line_num']:4d}: {row['original_line']}\n")
    
    # 可视化对比
    plt.figure(figsize=(15, 10))
    
    # 原始数据
    plt.subplot(2, 1, 1)
    plt.scatter(range(len(df)), df['value'], alpha=0.6, s=20, color='blue', label='原始数据')
    plt.scatter(anomalies, df.iloc[anomalies]['value'], color='red', s=50, label='异常点')
    plt.title('原始数据 (包含异常点)')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 清理后数据
    plt.subplot(2, 1, 2)
    plt.scatter(range(len(clean_df)), clean_df['value'], alpha=0.6, s=20, color='green', label='清理后数据')
    plt.title('清理后数据 (移除异常点)')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data_cleaning_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return clean_df, anomaly_df

if __name__ == "__main__":
    print("数据异常检测与清理工具")
    print("=" * 50)
    
    clean_data, anomalies = detect_and_remove_anomalies()
    
    print(f"\n处理完成！")
    print(f"- 清理后的数据已保存到: filtered_comments_cleaned.txt")
    print(f"- 异常数据记录已保存到: anomalies_removed.txt")
    print(f"- 对比图表已保存到: data_cleaning_comparison.png")