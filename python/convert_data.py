import datetime
import json

def convert_txt_to_js():
    """将filtered_comments.txt转换为JavaScript数据文件"""
    
    data = []
    
    try:
        with open('filtered_comments.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        for line in lines:
            line = line.strip()
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    timestamp_str = parts[0]
                    fans_str = parts[1]
                    
                    try:
                        # 解析时间戳
                        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        fans = float(fans_str)
                        
                        # 过滤异常数据
                        if fans > 0 and fans < 10000:  # 粉丝数应该在合理范围内
                            data.append({
                                'timestamp': timestamp.isoformat(),
                                'fans': fans,
                                'time': int(timestamp.timestamp() * 1000)  # JavaScript时间戳
                            })
                    except (ValueError, TypeError) as e:
                        print(f"跳过无效数据行: {line} - {e}")
                        continue
        
        # 按时间排序
        data.sort(key=lambda x: x['time'])
        
        print(f"成功转换 {len(data)} 条数据")
        
        # 生成JavaScript文件
        js_content = f"""// 自动生成的粉丝数据文件
// 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

const FANS_DATA = {json.dumps(data, indent=2, ensure_ascii=False)};

// 导出数据
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = FANS_DATA;
}}
"""
        
        with open('js/data.js', 'w', encoding='utf-8') as js_file:
            js_file.write(js_content)
            
        print("数据已成功转换为 js/data.js")
        
        # 显示数据统计
        if data:
            fans_values = [d['fans'] for d in data]
            print(f"数据统计:")
            print(f"  时间范围: {data[0]['timestamp']} 到 {data[-1]['timestamp']}")
            print(f"  粉丝数范围: {min(fans_values):.1f} - {max(fans_values):.1f} 万")
            print(f"  总降幅: {fans_values[0] - fans_values[-1]:.1f} 万")
        
    except FileNotFoundError:
        print("错误: 找不到 filtered_comments.txt 文件")
    except Exception as e:
        print(f"转换过程中出现错误: {e}")

if __name__ == "__main__":
    convert_txt_to_js()  # 修复了函数名