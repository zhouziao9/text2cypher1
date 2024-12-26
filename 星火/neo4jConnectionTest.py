from neo4j import GraphDatabase

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = '1234567890'  # 替换为您的实际密码

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def test_connection():
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS number")
            for record in result:
                print(record["number"])
        print("连接成功！")
    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    test_connection()
    driver.close()