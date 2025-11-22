"""
Business Documents Analyzer Module
Handles invoices, contracts, proposals, salary slips, reports, and office PDFs
"""
import json
import re
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from workflows import WorkflowProcessor


class BusinessDocsAnalyzer:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
        self.workflow = WorkflowProcessor(openai_key)
    
    def detect_document_type(self, retriever) -> str:
        """Detect the type of business document"""
        template = """Identify the type of this business document.
        
Document: {context}

Is this an: Invoice, Contract, Proposal, Salary Slip, Report, or Other Office Document?

Return ONLY the document type name.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("document") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:3000]})
        doc_type = result.strip().lower()
        
        if "invoice" in doc_type:
            return "Invoice"
        elif "contract" in doc_type:
            return "Contract"
        elif "proposal" in doc_type:
            return "Proposal"
        elif "salary" in doc_type or "payroll" in doc_type:
            return "Salary Slip"
        elif "report" in doc_type:
            return "Report"
        else:
            return "Office Document"
    
    def extract_tables(self, retriever) -> List[Dict[str, Any]]:
        """Extract tables and line items from document"""
        template = """Extract all tables, line items, and structured data from this document.
        
Document: {context}

Return a JSON array of tables, each with:
- tableName: name/description of the table
- headers: [array of column headers]
- rows: [array of row objects with column values]
- totalAmount: total amount if applicable
- currency: currency code if applicable

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("document") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def analyze_business_doc(self, retriever) -> Dict[str, Any]:
        """Comprehensive business document analysis"""
        doc_type = self.detect_document_type(retriever)
        tables = self.extract_tables(retriever)
        insights = self.workflow.extract_insights(retriever, doc_type.lower())
        risk_analysis = self.workflow.produce_risk_analysis(retriever)
        action_items = self.workflow.generate_action_items(retriever)
        
        # Extract negotiation points for contracts
        negotiation_points = []
        if doc_type == "Contract":
            template = """Identify negotiation points and key terms in this contract.
            
Contract: {context}
            
Return a JSON object with:
- keyTerms: [list of important terms]
- negotiationPoints: [list of points that could be negotiated]
- redFlags: [list of concerning clauses]
- favorableTerms: [list of favorable terms]

Return ONLY valid JSON, no additional text.
"""
            
            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)
            
            docs = retriever.get_relevant_documents("contract") if hasattr(retriever, 'get_relevant_documents') else []
            content = format_docs(docs) if docs else ""
            
            prompt = PromptTemplate.from_template(template)
            chain = prompt | self.llm | self.output_parser
            
            result = chain.invoke({"context": content[:5000]})
            
            try:
                if result.strip().startswith('{'):
                    negotiation_points = json.loads(result)
                else:
                    import re
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        negotiation_points = json.loads(json_match.group())
            except:
                pass
        
        return {
            "documentType": doc_type,
            "summary": insights.get("summary", ""),
            "tables": tables,
            "insights": insights,
            "risks": risk_analysis.get("risks", []),
            "redFlags": risk_analysis.get("risks", []),
            "actionItems": action_items,
            "negotiationPoints": negotiation_points.get("negotiationPoints", []) if negotiation_points else [],
            "keyTerms": negotiation_points.get("keyTerms", []) if negotiation_points else []
        }


