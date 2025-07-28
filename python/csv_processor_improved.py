import csv
import re
import glob
from datetime import datetime, timezone, timedelta
from collections import defaultdict

def timestamp_to_beijing_time(timestamp_str):
    """将UTC时间戳转换为北京时间"""
    try:
        # 抖音后台存储的是UTC+0时间戳，需要转换为北京时间(UTC+8)
        timestamp = int(timestamp_str)
        
        # 创建UTC时间
        utc_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        # 转换为北京时间 (UTC+8)
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = utc_time.astimezone(beijing_tz)
        
        return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, OSError) as e:
        print(f"时间戳转换错误: {timestamp_str}, 错误: {e}")
        return None

def extract_number_from_comment(comment):
    """从评论中提取数字，优先提取纯数字，处理'目前'后跟数字的情况"""
    found_numbers = []
    
    # 1. 优先提取纯数字（不带万字）
    pure_number_pattern = r'\b(\d{4}(?:\.\d+)?)\b'
    pure_matches = re.findall(pure_number_pattern, comment)
    for match in pure_matches:
        number = float(match)
        if 1800 <= number <= 2400.9 and number != 2000:
            found_numbers.append(number)
    
    # 2. 如果没有找到纯数字，提取带万字的数字
    if not found_numbers:
        million_pattern = r'(\d{4}(?:\.\d+)?)(?:万|w)'
        million_matches = re.findall(million_pattern, comment)
        for match in million_matches:
            number = float(match)
            if 1800 <= number <= 2400.9 and number != 2000:
                found_numbers.append(number)
    
    # 3. 处理'目前'后跟数字的情况（如：目前粉丝数1989w -> 1989）
    current_pattern = r'目前.*?(\d{4}(?:\.\d+)?)(?:万|w)?'
    current_matches = re.findall(current_pattern, comment)
    for match in current_matches:
        number = float(match)
        if 1800 <= number <= 2400.9 and number != 2000:
            found_numbers.append(number)
    
    return found_numbers

def contains_blocked_keywords(comment):
    """检查评论是否包含被屏蔽的关键词"""
    blocked_keywords = [
        '2000万', '2000w', '2000.0万', '2000.0w',  # 2000万相关
        '突破', '破', '冲破', '打破', '超越', '超过',  # 突破相关
        '达到', '到达', '抵达', '冲到', '冲击',  # 达到相关
        '新高', '历史', '记录', '最高', '峰值',  # 记录相关
        '里程碑', '节点', '关口', '大关',  # 里程碑相关
        # 年份相关关键词
        '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025',
        '现在', '今年', '去年', '明年', '回不去',
        '现在是几年',  # 新增
    ]
    
    # 先检查普通关键词
    for keyword in blocked_keywords:
        if keyword in comment:
            return True
    
    # 检查年份相关的正则表达式模式
    year_patterns = [
        r'20\d{2}年',  # 匹配2018年、2024年等
        r'现在20\d{2}',  # 匹配"现在2024"等
        r'等.{0,10}的人?',  # 匹配"等xxx的人"、"等2026的"等
        r'等.{0,10}那些人',  # 匹配"等xxx那些人"
    ]
    
    for pattern in year_patterns:
        if re.search(pattern, comment):
            return True
    
    return False

def calculate_confidence(comment, number):
    """计算评论的置信度，纯数字置信度最高"""
    confidence = 0
    
    # 基础置信度：数字在合理范围内
    if 1800 <= number <= 2400.9:
        confidence += 50
    
    # 数字格式加分 - 纯数字置信度最高
    number_str = str(number).rstrip('0').rstrip('.')  # 去掉末尾的0和小数点
    if number_str in comment and not re.search(f'{number_str}[万w]', comment):
        confidence += 40  # 纯数字最高分
    elif f"{number}万" in comment or f"{number}w" in comment:
        confidence += 25  # 带万字
    
    # "目前"后跟数字的情况，置信度较高
    if re.search(r'目前.*?' + str(number), comment):
        confidence += 30
    
    # 实时报数相关评论，置信度较高
    if re.search(r'(实时报数|报数|下一位|继续报)', comment):
        confidence += 25
    
    # 评论长度加分（简短评论通常更可信）
    if len(comment) <= 8:
        confidence += 25
    elif len(comment) <= 12:
        confidence += 15
    elif len(comment) <= 15:
        confidence += 5
    
    # 包含小数点的数字更精确，加分
    if '.' in str(number):
        confidence += 20
    
    # 减分项：包含不确定词汇
    uncertain_words = ['大概', '约', '左右', '差不多', '估计', '可能', '应该']
    for word in uncertain_words:
        if word in comment:
            confidence -= 15
    
    # 减分项：包含表情符号
    emoji_pattern = r'[\[\]（）()【】]'
    if re.search(emoji_pattern, comment):
        confidence -= 10
    
    return max(0, confidence)  # 确保置信度不为负

def is_valid_comment(comment):
    """检查评论是否符合筛选条件"""
    # 条件1：整条评论字数不大于15字
    if len(comment) > 15:
        return False
    
    # 条件2：检查是否包含被屏蔽的关键词
    if contains_blocked_keywords(comment):
        return False
    
    # 条件3：评论内容必须包含1800-2400.9之间的数字（排除2000）
    numbers = extract_number_from_comment(comment)
    if not numbers:
        return False
    
    # 条件4：如果评论包含两组数字直接排除
    if len(numbers) > 1:
        return False
    
    # 条件5：中文字符不超过6字
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', comment)
    if len(chinese_chars) > 6:
        return False
    
    return True

def process_single_csv_file(input_file):
    """处理单个CSV文件，返回有效记录列表"""
    valid_records = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                comment = row['content']
                create_time = row['create_time']
                
                # 检查评论是否符合条件
                if is_valid_comment(comment):
                    # 转换时间格式（修正时区）
                    formatted_time = timestamp_to_beijing_time(create_time)
                    if formatted_time:
                        # 提取数字
                        numbers = extract_number_from_comment(comment)
                        if numbers:
                            number = numbers[0]  # 取第一个数字
                            confidence = calculate_confidence(comment, number)
                            # 保存时间戳用于排序，格式化时间用于输出，包含置信度和原评论
                            valid_records.append((
                                int(create_time), 
                                formatted_time, 
                                number, 
                                confidence, 
                                comment
                            ))
    
    except Exception as e:
        print(f"读取CSV文件 {input_file} 时出错: {e}")
        return []
    
    return valid_records

def filter_same_time_records(records):
    """过滤同一时间的记录，保留置信度最高的"""
    # 按时间戳分组
    time_groups = defaultdict(list)
    for record in records:
        timestamp, formatted_time, number, confidence, comment = record
        time_groups[timestamp].append(record)
    
    filtered_records = []
    
    for timestamp, group in time_groups.items():
        if len(group) == 1:
            # 只有一条记录，直接保留
            filtered_records.append(group[0])
        else:
            # 多条记录，选择置信度最高的
            best_record = max(group, key=lambda x: x[3])  # 按置信度排序
            filtered_records.append(best_record)
    
    return filtered_records

def process_all_csv_files():
    """处理目录下所有CSV文件，生成两个输出文件"""
    # 获取当前目录下所有CSV文件
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        print("当前目录下没有找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件:")
    for file in csv_files:
        print(f"  - {file}")
    
    all_valid_records = []
    
    # 处理每个CSV文件
    for csv_file in csv_files:
        print(f"正在处理: {csv_file}")
        records = process_single_csv_file(csv_file)
        all_valid_records.extend(records)
        print(f"  从 {csv_file} 中提取了 {len(records)} 条有效记录")
    
    print(f"\n过滤前总记录数: {len(all_valid_records)}")
    
    # 过滤同一时间的记录
    filtered_records = filter_same_time_records(all_valid_records)
    print(f"过滤同一时间记录后: {len(filtered_records)}")
    
    # 按时间戳排序
    filtered_records.sort(key=lambda x: x[0])
    
    # 写入两个文件
    try:
        # 文件1：只包含数字和时间
        with open("filtered_comments_numbers_only.txt", 'w', encoding='utf-8') as txtfile:
            for timestamp, formatted_time, number, confidence, comment in filtered_records:
                txtfile.write(f"{formatted_time}\t{number}\n")
        
        # 文件2：包含原评论、数字和时间
        with open("filtered_comments_with_original.txt", 'w', encoding='utf-8') as txtfile:
            for timestamp, formatted_time, number, confidence, comment in filtered_records:
                txtfile.write(f"{formatted_time}\t{number}\t{comment}\n")
        
        print(f"\n处理完成！共筛选出 {len(filtered_records)} 条符合条件的评论")
        print(f"结果已按北京时间顺序保存到:")
        print(f"  - filtered_comments_numbers_only.txt (仅数字和时间)")
        print(f"  - filtered_comments_with_original.txt (包含原评论)")
        
        # 显示一些统计信息
        print(f"\n统计信息:")
        print(f"- 数字范围：1800-2400.9（排除2000）")
        print(f"- 已修正时区：UTC+0 -> 北京时间(UTC+8)")
        print(f"- 纯数字置信度最高，排除2000")
        print(f"- 处理了'目前'后跟数字的情况")
        print(f"- 保留了'实时报数'相关评论")
        print(f"- 排除了年份相关评论（如'2018回不去了'、'现在2024年'）")
        print(f"- 排除了'等xxx的人'类型评论")
        print(f"- 屏蔽了包含'2000万'和'突破'等关键词的评论")
        print(f"- 对同一时间的多条评论选择了置信度最高的记录")
        
        # 显示置信度分布
        confidences = [record[3] for record in filtered_records]
        if confidences:
            print(f"- 平均置信度: {sum(confidences)/len(confidences):.1f}")
            print(f"- 最高置信度: {max(confidences)}")
            print(f"- 最低置信度: {min(confidences)}")
        
    except Exception as e:
        print(f"写入文件时出错: {e}")

def main():
    print("改进版CSV处理器 - 修复'等xxx的人'过滤问题")
    print("新增功能:")
    print("1. 数字范围：1800-2400.9（排除2000）")
    print("2. 修正时区：抖音UTC+0时间戳 -> 北京时间(UTC+8)")
    print("3. 纯数字置信度最高")
    print("4. 处理'目前'后跟数字的情况（如：目前粉丝数1933.2 -> 1933.2）")
    print("5. 保留'实时报数'相关评论")
    print("6. 排除年份相关评论（如'2018回不去了'、'现在2024年'）")
    print("7. 修复：正确排除'等xxx的人'类型评论")
    print("8. 生成两个文件：仅数字+时间 和 包含原评论")
    print("=" * 70)
    
    process_all_csv_files()

if __name__ == "__main__":
    main()