import requests
import json
from neo4j import GraphDatabase
import csv
import time
import re

# 定义腾讯混元大模型的 API URL
url = ''

# 定义请求头，请替换为您的实际 Authorization 令牌
headers = {
    '  # 替换为您的实际令牌
}

# 定义 assistant_id 和 user_id，请替换为您的实际值
assistant_id = ''
user_id = ''

# 连接到 Neo4j 数据库
uri = "bolt://localhost:7687"
username = "neo4j"
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

# 定义测试用例列表
test_cases = [
    {
        "question": "找出所有出演了《黑客帝国》的演员。",
        "correct_query": "MATCH (a:Person)-[:ACTED_IN]->(m:Movie {title: 'The Matrix'}) RETURN a.name"
    },
    {
        "question": "导演是 'Christopher Nolan' 的电影有哪些？",
        "correct_query": "MATCH (d:Person {name: 'Christopher Nolan'})-[:DIRECTED]->(m:Movie) RETURN m.title"
    },
    {
        "question": "查找1995年发行的电影。",
        "correct_query": "MATCH (m:Movie {released: 1995}) RETURN m.title"
    },

    {
        "question": "Find all movies Tom Hanks acted in.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.released ORDER BY m.released ASC LIMIT 1;"
    },
    {
        "question": "Find the earliest movie Tom Hanks acted in.",
        "correct_query": "MATCH (p:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.released ORDER BY m.released ASC LIMIT 1;"
    },
    {
        "question": "Who directed the movie 'The Matrix'?",
        "correct_query": "MATCH (m:Movie {title: 'The Matrix'})<-[:DIRECTED]-(d:Person) RETURN d.name;"
    },
    {
        "question": "Find all movies released in the year 2000.",
        "correct_query": "MATCH (m:Movie) WHERE m.released = 2000 RETURN m.title;"
    },
    {
        "question": "Find the highest-rated movie Tom Hanks acted in.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.imdbRating ORDER BY m.imdbRating DESC LIMIT 1;"
    },
    {
        "question": "Find all actors in 'The Matrix'.",
        "correct_query": "MATCH (m:Movie {title: 'The Matrix'})<-[:ACTED_IN]-(a:Person) RETURN a.name;"
    },
    {
        "question": "Find all movies released in 1999 and their directors.",
        "correct_query": "MATCH (m:Movie {released: 1999})-[:DIRECTED]->(d:Person) RETURN m.title, d.name;"
    },
    {
        "question": "Find all directors Tom Hanks has worked with.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person) RETURN DISTINCT d.name;"
    },
    {
        "question": "Find all movies that have more than 5 actors.",
        "correct_query": """MATCH (m:Movie)<-[:ACTED_IN]-(a:Person)
            WITH m, COUNT(a) AS actorCount
            WHERE actorCount > 5
            RETURN m.title, actorCount;"""
    },
    # {
    #     "question": "Find all movies and their directors with IMDb ratings.",
    #     "correct_query": """MATCH (m:Movie)-[:DIRECTED]->(d:Person)
    #     RETURN m.title, d.name, m.imdbRating;"""
    # },
    {
        "question": "Find all movies Tom Hanks acted in after the year 2000.",
        "correct_query": """MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)
            WHERE m.released > 2000
            RETURN m.title, m.released;"""
    },
    {
        "question": "Find the IMDb rating and release year of 'The Matrix'.",
        "correct_query": """MATCH (m:Movie {title: 'The Matrix'})
            RETURN m.imdbRating, m.released;"""
    },
    {
        "question": "Find all movies and their writers.",
        "correct_query": "MATCH (m:Movie)-[:WRITTEN_BY]->(w:Person) RETURN m.title, w.name;"
    },
    {
        "question": "How many movies has Tom Hanks acted in?",
        "correct_query": """MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)
            RETURN COUNT(m) AS movieCount;"""
    },
    {
        "question": "Find the highest-rated movie and its director.",
        "correct_query": """MATCH (m:Movie)-[:DIRECTED]->(d:Person)
            RETURN m.title, d.name, m.imdbRating
    ORDER BY m.imdbRating DESC
    LIMIT 1;"""
    },
    {
        "question": "Find the director who has worked with Tom Hanks the most and count the number of their movies together.",
        "correct_query": """MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person)
            WITH d, COUNT(m) AS collaborations
            ORDER BY collaborations DESC
            LIMIT 1
            RETURN d.name, collaborations;"""
    },
    {
        "question": "Find the top 10 highest-rated movies and their directors.",
        "correct_query": """MATCH (m:Movie)-[:DIRECTED]->(d:Person)
            RETURN m.title, d.name, m.imdbRating
    ORDER BY m.imdbRating DESC
    LIMIT 10;"""
    },
    {
        "question": "Find the five lowest-rated movies released after 2000.",
        "correct_query": """MATCH (m:Movie)
            WHERE m.released > 2000
            RETURN m.title, m.imdbRating
            ORDER BY m.imdbRating ASC
            LIMIT 5;"""
    },
    {
        "question": "Find all actors who have acted in more than 10 movies and count their movies.",
        "correct_query": """MATCH (a:Person)-[:ACTED_IN]->(m:Movie)
            WITH a, COUNT(m) AS movieCount
            WHERE movieCount > 10
            RETURN a.name, movieCount
    ORDER BY movieCount DESC;"""
    },
    {
        "question": "Find the top 3 actors who have worked with Tom Hanks the most and count their collaborations.",
        "correct_query": """MATCH (a:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(t:Person {name: 'Tom Hanks'})
            WITH a, COUNT(m) AS collaborations
            ORDER BY collaborations DESC
            LIMIT 3
            RETURN a.name, collaborations;"""
    },
    {
        "question": "Find the highest and lowest-rated movies directed by the same director.",
        "correct_query": "MATCH (d:Person)-[:DIRECTED]->(m:Movie) WITH d, m ORDER BY m.imdbRating DESC WITH d, COLLECT(m)[0] AS highestRated, COLLECT(m)[-1] AS lowestRated RETURN d.name, highestRated.title AS highestRatedMovie, highestRated.imdbRating AS highestRating, lowestRated.title AS lowestRatedMovie, lowestRated.imdbRating AS lowestRating;"
    },
    {
        "question": "Find the director who has worked with Keanu Reeves the most and count their movies together.",
        "correct_query": "MATCH (a:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person) WITH d, COUNT(m) AS collaborations ORDER BY collaborations DESC LIMIT 1 RETURN d.name, collaborations;"
    },
    {
        "question": "Find the highest-grossing movie released between 2010 and 2020.",
        "correct_query": "MATCH (m:Movie) WHERE m.released >= 2010 AND m.released <= 2020 RETURN m.title, m.boxOffice ORDER BY m.boxOffice DESC LIMIT 1;"
    },
    {
        "question": "Find all movies directed by multiple directors and return their IMDb ratings.",
        "correct_query": "MATCH (m:Movie)-[:DIRECTED]->(d:Person) WITH m, COUNT(d) AS directorCount WHERE directorCount > 1 RETURN m.title, m.imdbRating;"
    },
    {
        "question": "Find the earliest movie Keanu Reeves acted in.",
        "correct_query": "MATCH (a:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.released ORDER BY m.released ASC LIMIT 1;"
    },
    {
        "question": "Find the director who has worked with Tom Hanks the most and count their collaborations.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person) WITH d, COUNT(m) AS collaborations ORDER BY collaborations DESC LIMIT 1 RETURN d.name, collaborations;"
    },
    {
        "question": "Find all movies released in 1995.",
        "correct_query": "MATCH (m:Movie) WHERE m.released = 1995 RETURN m.title;"
    },
    {
        "question": "Find the top 5 highest-rated movies.",
        "correct_query": "MATCH (m:Movie) RETURN m.title, m.imdbRating ORDER BY m.imdbRating DESC LIMIT 5;"
    },
    {
        "question": "Find the lowest-rated movie Keanu Reeves acted in.",
        "correct_query": "MATCH (a:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.imdbRating ORDER BY m.imdbRating ASC LIMIT 1;"
    },
    {
        "question": "Find the 10 lowest-rated movies released after 2000.",
        "correct_query": "MATCH (m:Movie) WHERE m.released > 2000 RETURN m.title, m.imdbRating ORDER BY m.imdbRating ASC LIMIT 10;"
    },
    {
        "question": "Find all movies released between 2000 and 2005.",
        "correct_query": "MATCH (m:Movie) WHERE m.released >= 2000 AND m.released <= 2005 RETURN m.title;"
    },
    {
        "question": "Find the actor who has worked with Tom Hanks the most times.",
        "correct_query": "MATCH (a:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(t:Person {name: 'Tom Hanks'}) WITH a, COUNT(m) AS collaborations ORDER BY collaborations DESC LIMIT 1 RETURN a.name;"
    },
    {
        "question": "Find the IMDb ratings of all movies in the 'The Matrix' series.",
        "correct_query": "MATCH (m:Movie) WHERE m.title STARTS WITH 'The Matrix' RETURN m.title, m.imdbRating;"
    },
    {
        "question": "Find the highest-grossing movie released after 2000.",
        "correct_query": "MATCH (m:Movie) WHERE m.released > 2000 RETURN m.title, m.boxOffice ORDER BY m.boxOffice DESC LIMIT 1;"
    },
    {
        "question": "Find all movies Tom Hanks acted in and their IMDb ratings.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.imdbRating;"
    },
    {
        "question": "Find all movies released in 1995 and their actors.",
        "correct_query": "MATCH (m:Movie {released: 1995})<-[:ACTED_IN]-(a:Person) RETURN m.title, a.name;"
    },
    {
        "question": "Find the highest-rated movie released in 1995.",
        "correct_query": "MATCH (m:Movie) WHERE m.released = 1995 RETURN m.title, m.imdbRating ORDER BY m.imdbRating DESC LIMIT 1;"
    },
    {
        "question": "Find the highest-grossing movie that Tom Hanks acted in.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.boxOffice ORDER BY m.boxOffice DESC LIMIT 1;"
    },
    {
        "question": "Find all directors who have worked with Keanu Reeves.",
        "correct_query": "MATCH (a:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person) RETURN DISTINCT d.name;"
    },
    {
        "question": "Find the highest-rated movie released after 2000 and its director.",
        "correct_query": "MATCH (m:Movie)-[:DIRECTED]->(d:Person) WHERE m.released > 2000 RETURN m.title, d.name, m.imdbRating ORDER BY m.imdbRating DESC LIMIT 1;"
    },
    {
        "question": "Find the actor who has worked with Keanu Reeves the most times.",
        "correct_query": "MATCH (a:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(k:Person {name: 'Keanu Reeves'}) WITH a, COUNT(m) AS collaborations ORDER BY collaborations DESC LIMIT 1 RETURN a.name;"
    },
    {
        "question": "Find all movies written by two or more writers.",
        "correct_query": "MATCH (m:Movie)-[:WRITTEN_BY]->(w:Person) WITH m, COUNT(w) AS writerCount WHERE writerCount >= 2 RETURN m.title;"
    },
    {
        "question": "Find all movies released after 2010.",
        "correct_query": "MATCH (m:Movie) WHERE m.released > 2010 RETURN m.title;"
    },
    {
        "question": "Find the lowest-grossing movie that Tom Hanks acted in.",
        "correct_query": "MATCH (a:Person {name: 'Tom Hanks'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.boxOffice ORDER BY m.boxOffice ASC LIMIT 1;"
    },
    {
        "question": "Find all directors who have worked with Keanu Reeves more than twice.",
        "correct_query": "MATCH (a:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Person) WITH d, COUNT(m) AS collaborations WHERE collaborations > 2 RETURN d.name;"
    }
]

results = []

for case in test_cases:
    question = case["question"]
    correct_query = case["correct_query"]

    # 构建系统消息内容，添加示例
    system_content = """你是一个将自然语言问题转换为 Cypher 查询的助手。你的任务是根据用户提供的自然语言问题，生成对应的 Cypher 查询语句。

以下是一些示例：

示例1：

自然语言问题：
"找出所有出演了《黑客帝国》的演员。"

Cypher 查询：
MATCH (a:Person)-[:ACTED_IN]->(m:Movie {title: 'The Matrix'}) RETURN a.name;

示例2：

自然语言问题：
"导演是 'Christopher Nolan' 的电影有哪些？"

Cypher 查询：
MATCH (d:Person {name: 'Christopher Nolan'})-[:DIRECTED]->(m:Movie) RETURN m.title;

示例3：

自然语言问题：
"查找1995年发行的电影。"

Cypher 查询：
MATCH (m:Movie {released: 1995}) RETURN m.title;

请根据上述示例，将以下自然语言问题转换为 Cypher 查询。只需输出 Cypher 查询语句，不要添加其他内容。
"""

    # 定义请求体
    data = {
        "assistant_id": assistant_id,
        "user_id": user_id,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{system_content}\n自然语言问题：\n\"{question}\"\n\nCypher 查询："
                    }
                ]
            }
        ]
    }

    # 发送 POST 请求
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        print(f"响应状态码：{response.status_code}")
        print(f"响应内容：{response.text}")  # 打印响应内容
        if response.status_code == 200:
            break
        else:
            print(f"请求失败，状态码：{response.status_code}，信息：{response.text}")
            # 从错误信息中提取等待时间
            match = re.search(r'please try again after (\d+) seconds', response.text)
            if match:
                retry_after = int(match.group(1))
            else:
                retry_after = retry_delay
            if attempt < max_retries - 1:
                print(f"等待 {retry_after} 秒后重试...")
                time.sleep(retry_after)
                continue
            else:
                print("已达到最大重试次数。")
                break

    # 处理响应
    if response.status_code != 200:
        generated_query = ""
    else:
        response_json = response.json()
        # 检查响应中是否有错误信息
        if 'error' in response_json:
            print(f"API 返回错误：{response_json['error']}")
            generated_query = ""
        elif 'choices' in response_json and len(response_json['choices']) > 0:
            message = response_json['choices'][0]['message']
            if 'content' in message:
                generated_query = message['content']
                # 去除首尾空白字符，替换中间的换行符
                generated_query = generated_query.strip().replace('\\n', '').replace('\n', '')
            else:
                print("响应中没有 'content' 字段")
                generated_query = ""
        else:
            print("无法解析 API 的响应内容。")
            generated_query = ""

    # 打印生成的查询，便于调试
    print(f"自然语言问题：{question}")
    print(f"生成的查询：\n{generated_query}\n")

    # 执行正确的查询
    try:
        correct_output = run_query(correct_query)
    except Exception as e:
        correct_output = f"错误：{str(e)}"

    # 执行模型生成的查询
    try:
        if generated_query.strip():
            generated_output = run_query(generated_query.strip())
        else:
            generated_output = "生成的查询为空，无法执行。"
    except Exception as e:
        generated_output = f"错误：{str(e)}"

    # 比较输出结果是否一致，并计算准确率
    if isinstance(correct_output, list) and isinstance(generated_output, list):
        # 比较列表长度
        total_rows = max(len(correct_output), len(generated_output))
        if total_rows > 0:
            # 逐行比较
            match_count = 0
            for co, go in zip(correct_output, generated_output):
                if co == go:
                    match_count += 1
            accuracy = (match_count / total_rows) * 100
        else:
            accuracy = 0.0
    else:
        # 如果有错误，则准确率为 0
        accuracy = 0.0

    # 将准确率保留两位小数
    accuracy = round(accuracy, 2)

    # 将结果添加到列表中
    results.append({
        "question": question,
        "correct_query": correct_query,
        "generated_query": generated_query.strip(),
        "correct_output": correct_output,
        "generated_output": generated_output,
        "accuracy": f"{accuracy}%"  # 添加准确率
    })

    # 在每次请求后等待一段时间，避免触发速率限制
    time.sleep(1.5)

# 将结果写入 CSV 文件
with open('movies_test_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ["question", "correct_query", "generated_query", "correct_output", "generated_output", "accuracy"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)


    writer.writeheader()
    for result in results:
        writer.writerow(result)
total_accuracy = sum(float(result["accuracy"].strip('%')) for result in results) / len(results)
print(f"总体准确率：{total_accuracy:.2f}%")