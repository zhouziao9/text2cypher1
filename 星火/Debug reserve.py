import os
from neo4j import GraphDatabase
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

# 直接在代码中包含星火大模型API密钥（不推荐）
SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
SPARKAI_APP_ID = '1764ad84'
SPARKAI_API_SECRET = 'MzU0ZGY5ZDdkZTE2ZTUxYzdlOTliNTU2'
SPARKAI_API_KEY = 'af689c49fb6dc19c139d9af894d07405'
SPARKAI_DOMAIN = '4.0Ultra'

# 直接在代码中包含Neo4j数据库连接信息（不推荐）
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'root123456'  # 替换为您设置的新密码

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def natural_language_to_cypher_spark(nl_query):
    """
    使用星火大模型将自然语言查询转换为Cypher查询，并避免使用已弃用的id函数。
    """
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    messages = [ChatMessage(
        role="user",
        content=f"将以下自然语言查询转换为Cypher查询语句:\n\n自然语言查询: {nl_query}\n\nCypher查询:"
    )]
    handler = ChunkPrintHandler()
    try:
        response = spark.generate([messages], callbacks=[handler])
        cypher_query = None

        if hasattr(response, 'generations') and len(response.generations) > 0:
            for i, generation_list in enumerate(response.generations):
                for j, generation in enumerate(generation_list):
                    if hasattr(generation, 'text'):
                        cypher_query = generation.text.strip()
                        # 检查是否使用了 id(n)，如果有，将其替换为基于属性的查询
                        if "id(n)" in cypher_query:
                            print("发现已弃用的 id(n) 查询，进行替换...")
                            cypher_query = cypher_query.replace("id(n)", "n.id")
                        print(f"从 Generation {i}-{j} 提取到的 Cypher 查询: {cypher_query}")
                        break
                    elif hasattr(generation, 'message') and hasattr(generation.message, 'content'):
                        cypher_query = generation.message.content.strip()
                        print(f"从 Generation {i}-{j} 提取到的 Cypher 查询: {cypher_query}")
                        break
                    elif hasattr(generation, 'content'):
                        cypher_query = generation.content.strip()
                        print(f"从 Generation {i}-{j} 提取到的 Cypher 查询: {cypher_query}")
                        break
                    else:
                        print(f"Generation {i}-{j} 中没有找到 'text'、'message.content' 或 'content' 属性。")
                if cypher_query:
                    break
        return cypher_query
    except Exception as e:
        print(f"生成Cypher查询时出错: {e}")
        return None

def execute_cypher_query(cypher_query):
    """
    在Neo4j数据库中执行Cypher查询并返回结果。
    """
    with driver.session() as session:
        try:
            result = session.run(cypher_query)
            return [record.data() for record in result]
        except Exception as e:
            print(f"执行Cypher查询时出错: {e}")
            return None

def main():
    print("自然语言到Cypher查询转换系统")
    print("输入'退出'以结束程序。")

    while True:
        nl_query = input("\n请输入自然语言查询: ")
        if nl_query.strip().lower() == "退出":
            break

        print("正在生成Cypher查询...")
        cypher_query = natural_language_to_cypher_spark(nl_query)

        if cypher_query:
            print(f"\n生成的Cypher查询:\n{cypher_query}")
            print("正在执行查询...")
            results = execute_cypher_query(cypher_query)

            if results is not None:
                if len(results) > 0:
                    print("查询结果:")
                    for record in results:
                        print(record)
                else:
                    print("查询执行成功，但未找到匹配的结果。")
            else:
                print("查询执行失败。")
        else:
            print("无法生成Cypher查询。")

    driver.close()
    print("程序已结束。")

if __name__ == "__main__":
    main()