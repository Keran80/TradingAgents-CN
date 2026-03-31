"""
LLM 问答模块
支持多种 LLM：OpenAI、DeepSeek、智谱等
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from ..base import RetrievalResult, QaResult
from ..retriever import Retriever


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"  # openai, deepseek, zhipu, anthropic
    model: str = "gpt-3.5-turbo"
    api_key: str = ""
    api_base: str = ""  # 自定义 API 地址
    temperature: float = 0.7
    max_tokens: int = 2000


class BaseLLM:
    """LLM 基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送聊天请求"""
        raise NotImplementedError


class OpenAILLM(BaseLLM):
    """OpenAI LLM"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        import openai
        if config.api_key:
            openai.api_key = config.api_key
        if config.api_base:
            openai.api_base = config.api_base
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        import openai
        
        try:
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM 调用失败: {str(e)}"


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        import requests
        
        if not self.config.api_base:
            self.config.api_base = "https://api.deepseek.com/v1"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API 错误: {response.text}"
                
        except Exception as e:
            return f"LLM 调用失败: {str(e)}"


class ZhipuLLM(BaseLLM):
    """智谱 LLM"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        import requests
        
        if not self.config.api_base:
            self.config.api_base = "https://open.bigmodel.cn/api/paas/v4"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
            
            response = requests.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API 错误: {response.text}"
                
        except Exception as e:
            return f"LLM 调用失败: {str(e)}"


class AnthropicLLM(BaseLLM):
    """Anthropic Claude LLM"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        import requests
        
        if not self.config.api_base:
            self.config.api_base = "https://api.anthropic.com/v1"
        
        try:
            # 转换消息格式
            system_msg = ""
            filtered_messages = []
            for msg in messages:
                if msg['role'] == 'system':
                    system_msg = msg['content']
                else:
                    filtered_messages.append(msg)
            
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "system": system_msg,
                "messages": filtered_messages
            }
            
            response = requests.post(
                f"{self.config.api_base}/messages",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                return f"API 错误: {response.text}"
                
        except Exception as e:
            return f"LLM 调用失败: {str(e)}"


class QaSystem:
    """问答系统"""
    
    def __init__(
        self,
        retriever: Retriever,
        llm: BaseLLM = None,
        system_prompt: str = None
    ):
        self.retriever = retriever
        self.llm = llm
        self.system_prompt = system_prompt or (
            "你是一个专业的投资研究助手。根据给定的上下文信息回答用户的问题。"
            "如果上下文中没有相关信息，请明确告知用户。"
            "回答要准确、简洁、有条理。"
        )
    
    def ask(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True
    ) -> QaResult:
        """问答
        
        Args:
            question: 用户问题
            top_k: 检索的文档数量
            include_sources: 是否包含来源
        
        Returns:
            问答结果
        """
        # 检索相关文档
        results = self.retriever.search(question, top_k=top_k)
        
        if not results:
            return QaResult(
                question=question,
                answer="抱歉，我没有找到与您问题相关的文档信息。",
                sources=[],
                metadata={'status': 'no_results'}
            )
        
        # 构建上下文
        context = "\n\n".join([
            f"[文档 {i+1}]\n{r.chunk.content}"
            for i, r in enumerate(results)
        ])
        
        # 构建提示词
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""基于以下上下文信息回答问题：

{context}

问题：{question}

请根据上下文回答，如果上下文中没有相关信息，请说明。"""}
        ]
        
        # 调用 LLM
        if self.llm:
            answer = self.llm.chat(messages)
        else:
            # 没有 LLM 时返回检索结果摘要
            answer = f"检索到 {len(results)} 个相关文档：\n\n"
            for i, r in enumerate(results):
                answer += f"{i+1}. {r.chunk.content[:200]}...\n"
        
        return QaResult(
            question=question,
            answer=answer,
            sources=results if include_sources else [],
            metadata={
                'retrieved_docs': len(results),
                'top_score': results[0].score if results else 0
            }
        )
    
    def ask_streaming(self, question: str, top_k: int = 5):
        """流式问答（需要 LLM 支持流式输出）"""
        results = self.retriever.search(question, top_k=top_k)
        
        context = "\n\n".join([
            f"[文档 {i+1}]\n{r.chunk.content}"
            for i, r in enumerate(results)
        ])
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""基于以下上下文信息回答问题：

{context}

问题：{question}"""}
        ]
        
        if self.llm:
            # 如果 LLM 支持流式，返回迭代器
            for chunk in self.llm.chat_streaming(messages):
                yield chunk
        else:
            yield "请配置 LLM"


def get_llm(config: LLMConfig) -> BaseLLM:
    """获取 LLM 实例"""
    providers = {
        'openai': OpenAILLM,
        'deepseek': DeepSeekLLM,
        'zhipu': ZhipuLLM,
        'anthropic': AnthropicLLM,
    }
    
    llm_class = providers.get(config.provider, OpenAILLM)
    return llm_class(config)


def create_qa_system(
    retriever: Retriever,
    llm_provider: str = "deepseek",
    llm_model: str = "deepseek-chat",
    api_key: str = "",
    api_base: str = "",
    system_prompt: str = None
) -> QaSystem:
    """创建问答系统（便捷函数）"""
    config = LLMConfig(
        provider=llm_provider,
        model=llm_model,
        api_key=api_key,
        api_base=api_base
    )
    
    llm = get_llm(config)
    
    return QaSystem(
        retriever=retriever,
        llm=llm,
        system_prompt=system_prompt
    )