import json
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def analyze_qa_lengths(json_file_path):
    """
    分析QA JSON文件中问题和答案的长度分布
    
    Args:
        json_file_path (str): JSON文件路径
    """
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    # 提取问题和答案的长度
    question_lengths = []
    answer_lengths = []
    
    for item in qa_data:
        question_lengths.append(len(item['question']))
        answer_lengths.append(len(item['answer']))
    
    # 打印基本统计信息
    print(f"总QA对数量: {len(qa_data)}")
    print(f"问题长度统计:")
    print(f"  最小值: {min(question_lengths)}")
    print(f"  最大值: {max(question_lengths)}")
    print(f"  平均值: {np.mean(question_lengths):.2f}")
    print(f"  中位数: {np.median(question_lengths)}")
    
    print(f"\n答案长度统计:")
    print(f"  最小值: {min(answer_lengths)}")
    print(f"  最大值: {max(answer_lengths)}")
    print(f"  平均值: {np.mean(answer_lengths):.2f}")
    print(f"  中位数: {np.median(answer_lengths)}")
    
    # 绘制分布图
    plt.figure(figsize=(15, 10))
    
    # 问题长度分布
    plt.subplot(1, 2, 1)
    plt.hist(question_lengths, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.title('问题长度分布')
    plt.xlabel('字符数量')
    plt.ylabel('频次')
    plt.grid(True, alpha=0.3)
    
    # 答案长度分布
    plt.subplot(1, 2, 2)
    plt.hist(answer_lengths, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.title('答案长度分布')
    plt.xlabel('字符数量')
    plt.ylabel('频次')
    plt.grid(True, alpha=0.3)
    
    plt.show()
    
    return question_lengths, answer_lengths

# 使用示例
if __name__ == "__main__":
    # 替换为你的JSON文件路径
    json_file = "qa.json"
    
    try:
        q_lengths, a_lengths = analyze_qa_lengths(json_file)
        
        # 额外的详细分析
        print("\n" + "="*50)
        print("详细分析:")
        
        # 长度区间统计
        def count_by_ranges(lengths, ranges):
            counts = {}
            for range_label, (min_len, max_len) in ranges.items():
                counts[range_label] = sum(1 for l in lengths if min_len <= l < max_len)
            return counts
        
        ranges = {
            "很短(1-10)": (1, 10),
            "短(11-30)": (11, 30),
            "中等(31-100)": (31, 100),
            "长(101-300)": (101, 300),
            "很长(300+)": (300, 10000)
        }
        
        q_range_counts = count_by_ranges(q_lengths, ranges)
        a_range_counts = count_by_ranges(a_lengths, ranges)
        
        print("\n问题长度区间分布:")
        for range_label, count in q_range_counts.items():
            print(f"  {range_label}: {count}个 ({count/len(q_lengths)*100:.1f}%)")
            
        print("\n答案长度区间分布:")
        for range_label, count in a_range_counts.items():
            print(f"  {range_label}: {count}个 ({count/len(a_lengths)*100:.1f}%)")
            
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file}")
    except json.JSONDecodeError:
        print(f"错误: {json_file} 不是有效的JSON格式")
    except Exception as e:
        print(f"发生错误: {e}")
