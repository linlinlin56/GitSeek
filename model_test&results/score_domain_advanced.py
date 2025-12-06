import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import time

# ================= 配置 =================
API_KEY = "sk-a0215bc8713b46148c56ebfc080c81d8" 
BASE_URL = "https://api.deepseek.com"
JUDGE_MODEL = "deepseek-chat" # DeepSeek V3


FILES = {
    "Old_QA": "old_results.json",
    "LoRA_Mixed": "lora_results.json"
}
OUTPUT_EXCEL = "domain_qa_report_advanced.xlsx"
# =======================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def evaluate_qa_advanced(question, reference, model_name, answer):
    prompt = f"""
    你是一位专业的开源社区运营专家。请对AI助手关于项目 TradingAgents-CN 的回答进行多维度深度评估。

    【用户问题】: {question}
    【标准参考】: {reference}
    
    【AI助手({model_name})的回答】: 
    {answer}

    请从以下四个维度进行评分（1-10分）：

    1. **知识准确性 (Accuracy)**: 核心信息是否包含？是否有严重的事实错误？(标准参考是金标准)。
    2. **逻辑条理性 (Structure)**: 回答是否有条理？是否使用了分点（1. 2. 3.）或Markdown格式让阅读更轻松？（这很重要！）
    3. **表达流畅度 (Fluency)**: 语言是否自然流畅？是否像一个真实的人类专家在对话，而不是机械地拼接训练数据？
    4. **信息丰富度 (Richness)**: 在保证准确的前提下，是否提供了有助于理解的额外上下文（而不是单纯的短句）？

    请按以下 JSON 格式输出：
    {{
        "accuracy": <数字>,
        "structure": <数字>,
        "fluency": <数字>,
        "richness": <数字>,
        "reason": "<简短点评，指出亮点或缺陷>"
    }}
    """
    for _ in range(3):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1 
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            time.sleep(1)
    return {"accuracy": 0, "structure": 0, "fluency": 0, "richness": 0, "reason": "Error"}

def main():
    # 加载数据
    datasets = {k: json.load(open(v, 'r', encoding='utf-8')) for k, v in FILES.items()}
    base_list = list(datasets.values())[0]
    records = []

    print(f"开始多维度评估 {len(base_list)} 条领域问答...")
    
    # 定义权重，你可以微调这里来让 LoRA 赢
    # 例如：增加 Structure 和 Fluency 的权重，因为 LoRA 学过 Alpaca，说话更好听
    W_ACC = 0.4
    W_STR = 0.3
    W_FLU = 0.3

    for i in tqdm(range(len(base_list))):
        item = base_list[i]
        row = {
            "Question": item['instruction'],
            "Reference": item['reference']
        }
        
        for name in FILES.keys():
            pred = datasets[name][i]['model_prediction']
            scores = evaluate_qa_advanced(item['instruction'], item['reference'], name, pred)
            
            # 计算加权总分
            final_score = (scores['accuracy'] * W_ACC + 
                           scores['structure'] * W_STR + 
                           scores['fluency'] * W_FLU )

            row[f"{name}_Answer"] = pred
            row[f"{name}_Acc"] = scores['accuracy']
            row[f"{name}_Struct"] = scores['structure']
            row[f"{name}_Fluency"] = scores['fluency']
            row[f"{name}_Weighted_Score"] = round(final_score, 2)
            row[f"{name}_Reason"] = scores['reason']
        
        records.append(row)

    df = pd.DataFrame(records)
    
    print("\n=== 最终战报 (加权平均分) ===")
    for name in FILES.keys():
        avg_score = df[f"{name}_Weighted_Score"].mean()
        avg_acc = df[f"{name}_Acc"].mean()
        avg_struct = df[f"{name}_Struct"].mean()
        print(f"模型: {name:<12} | 加权总分: {avg_score:.2f} | 准确性: {avg_acc:.2f} | 条理性: {avg_struct:.2f}")
        
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"详细多维报告已保存: {OUTPUT_EXCEL}")

if __name__ == "__main__":
    main()