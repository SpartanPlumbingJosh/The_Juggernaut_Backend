"""
Prompt templates and chain structures for language model integration.
"""
from typing import Dict, List, Optional, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms.base import BaseLLM

class PromptTemplates:
    """Collection of prompt templates for different conversation scenarios."""
    
    @staticmethod
    def get_conversation_template() -> PromptTemplate:
        """
        Get the template for general conversation.
        
        Returns:
            PromptTemplate for conversation
        """
        template = """
        You are an advanced AI assistant designed to be helpful, harmless, and honest.
        
        Conversation History:
        {conversation_history}
        
        User: {user_input}
        
        Assistant:
        """
        
        return PromptTemplate(
            input_variables=["conversation_history", "user_input"],
            template=template.strip()
        )
    
    @staticmethod
    def get_knowledge_query_template() -> PromptTemplate:
        """
        Get the template for knowledge-based queries.
        
        Returns:
            PromptTemplate for knowledge queries
        """
        template = """
        You are an advanced AI assistant with access to a knowledge base.
        
        Conversation History:
        {conversation_history}
        
        User Query: {user_input}
        
        Relevant Knowledge:
        {knowledge_context}
        
        Provide a comprehensive and accurate response based on the relevant knowledge.
        
        Assistant:
        """
        
        return PromptTemplate(
            input_variables=["conversation_history", "user_input", "knowledge_context"],
            template=template.strip()
        )
    
    @staticmethod
    def get_system_instruction_template() -> PromptTemplate:
        """
        Get the template for system instructions.
        
        Returns:
            PromptTemplate for system instructions
        """
        template = """
        You are an advanced AI assistant designed to be helpful, harmless, and honest.
        
        System Instructions:
        {system_instructions}
        
        Conversation History:
        {conversation_history}
        
        User: {user_input}
        
        Assistant:
        """
        
        return PromptTemplate(
            input_variables=["system_instructions", "conversation_history", "user_input"],
            template=template.strip()
        )


class ChainBuilder:
    """Builder for creating LangChain chains with different configurations."""
    
    @staticmethod
    def build_conversation_chain(llm: BaseLLM) -> LLMChain:
        """
        Build a chain for general conversation.
        
        Args:
            llm: Language model to use in the chain
            
        Returns:
            LLMChain for conversation
        """
        prompt = PromptTemplates.get_conversation_template()
        return LLMChain(llm=llm, prompt=prompt)
    
    @staticmethod
    def build_knowledge_query_chain(llm: BaseLLM) -> LLMChain:
        """
        Build a chain for knowledge-based queries.
        
        Args:
            llm: Language model to use in the chain
            
        Returns:
            LLMChain for knowledge queries
        """
        prompt = PromptTemplates.get_knowledge_query_template()
        return LLMChain(llm=llm, prompt=prompt)
    
    @staticmethod
    def build_system_instruction_chain(llm: BaseLLM) -> LLMChain:
        """
        Build a chain with system instructions.
        
        Args:
            llm: Language model to use in the chain
            
        Returns:
            LLMChain with system instructions
        """
        prompt = PromptTemplates.get_system_instruction_template()
        return LLMChain(llm=llm, prompt=prompt)
