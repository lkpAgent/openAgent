import os
from openai import OpenAI

client = OpenAI(
    api_key= '864f980a5cf2b4ff16e1bb47beae15d0.gS1t9iDYqmETy1R2' , #  os.getenv("ZHIPU_API_KEY"),  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
    base_url="https://open.bigmodel.cn/api/paas/v4"  # 百炼服务的base_url
)

completion = client.embeddings.create(
    model="embedding-3",
    input='衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买',
    dimensions=1024, # 指定向量维度（仅 text-embedding-v3及 text-embedding-v4支持该参数）
    encoding_format="float"
)

print(completion.model_dump_json())