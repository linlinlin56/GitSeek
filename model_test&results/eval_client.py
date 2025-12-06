import json
import requests
from tqdm import tqdm

# ================= 配置 =================
# 你的测评数据文件路径
TEST_DATA_FILE = "/mnt/hdd/Haobin/nlp/test_general_20.json" 
# 结果保存路径 (会根据运行的模型不同自动加前缀)
OUTPUT_FILE_SUFFIX = "_results.json"
# 本地 API 地址 (ms-swift deploy 默认地址)
API_URL = "http://localhost:8002/v1/chat/completions"
MODEL_NAME = "repo_analyst" # 这个名字要和你部署时的 model_name 一致
# =======================================

def get_model_response(instruction, code_snippet=None):
    # 1. 拼接 Prompt (模拟你在侧边栏的操作)
    content = instruction
    if code_snippet and len(code_snippet.strip()) > 0:
        content = f"{instruction}\n\n【代码片段】:\n```python\n{code_snippet}\n```"

    # 2. 构造请求数据
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "你是一个专业的代码分析助手。"},
            {"role": "user", "content": content}
        ],
        "temperature": 0.1, # 测评时温度低一点，保证稳定
        "max_tokens": 2048,
        "stream": False
    }

    # 3. 发送请求
    try:
        response = requests.post(API_URL, json=payload).json()
        # 解析 OpenAI 格式的返回
        if 'choices' in response:
            return response['choices'][0]['message']['content']
        else:
            print(f"Error response: {response}")
            return "Error"
    except Exception as e:
        print(f"Request failed: {e}")
        return "Error"

def main():
    import sys
    # 从命令行参数获取当前跑的是什么模型 (base 或 lora)
    run_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    output_filename = f"{run_name}{OUTPUT_FILE_SUFFIX}"

    # 1. 读取数据
    print(f"正在读取测评数据: {TEST_DATA_FILE}")
    with open(TEST_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    print(f"开始对 {run_name} 模型进行批量推理 (共 {len(data)} 条)...")

    # 2. 批量推理
    for item in tqdm(data):
        # 获取 id, instruction, code, reference
        # 注意：确保你的 json 里字段名是对的
        instruction = item.get('instruction', '')
        code = item.get('code', '')
        
        # 调用 API
        prediction = get_model_response(instruction, code)
        
        # 保存结果
        result_item = item.copy()
        result_item['model_prediction'] = prediction
        results.append(result_item)

    # 3. 保存文件
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"推理完成！结果已保存至: {output_filename}")

if __name__ == "__main__":
    main()