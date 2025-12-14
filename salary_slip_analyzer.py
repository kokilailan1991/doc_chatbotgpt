"""
Professional Salary Slip Analyzer Module
Analyzes salary slips for payroll data, tax flags, mistakes, and SIP planning.
"""

import json
import re
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class SalarySlipAnalyzer:
    """Professional salary slip analysis system"""
    
    def __init__(self, openai_api_key: str):
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=openai_api_key)
        self.output_parser = StrOutputParser()
    
    def _create_chain(self, template: str, retriever):
        """Create LangChain chain for document analysis"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        def get_context(query):
            docs = retriever.get_relevant_documents(query) if hasattr(retriever, 'get_relevant_documents') else []
            return format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = (
            {"context": RunnablePassthrough() | get_context}
            | prompt
            | self.llm
            | self.output_parser
        )
        return chain
    
    def analyze_salary_slip(self, retriever) -> Dict[str, Any]:
        """Comprehensive salary slip analysis"""
        
        # Get summary
        summary = self._get_summary(retriever)
        
        # Extract salary data
        salary_data = self._extract_salary_data(retriever)
        
        # Extract expenses/deductions
        expenses_data = self._extract_expenses_data(retriever)
        
        # Analyze tax flags
        tax_flags = self._analyze_tax_flags(retriever, salary_data)
        
        # Find mistakes
        mistakes = self._find_mistakes(retriever, salary_data, expenses_data)
        
        # Calculate SIP recommendations
        sip_planning = self._calculate_sip_planning(salary_data, expenses_data)
        
        # Suggest savings
        savings_suggestions = self._suggest_savings(salary_data, expenses_data)
        
        return {
            "summary": summary,
            "salaryData": salary_data,
            "expensesData": expenses_data,
            "taxFlags": tax_flags,
            "mistakes": mistakes,
            "savingsSuggestions": savings_suggestions,
            "sipPlanning": sip_planning
        }
    
    def _get_summary(self, retriever) -> str:
        """Get summary of salary slip"""
        template = """Create a brief summary of this salary slip (2-3 sentences).

Context: {context}

Summary should include:
- Employee name/ID if available
- Gross salary and net pay
- Key deductions
- Month/year if mentioned

Summary:"""
        
        chain = self._create_chain(template, retriever)
        return chain.invoke("Summarize salary slip")
    
    def _extract_salary_data(self, retriever) -> List[Dict[str, str]]:
        """Extract salary/earnings components"""
        template = """Extract all salary/earnings components from this salary slip.

Context: {context}

Return a JSON array of salary components, each with:
- component: name (e.g., "Basic Salary", "HRA", "Allowances")
- amount: amount in currency format

Focus on:
- Basic Salary
- HRA (House Rent Allowance)
- Special Allowances
- Bonus
- Other Earnings

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("salary earnings basic HRA allowances") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _extract_expenses_data(self, retriever) -> List[Dict[str, str]]:
        """Extract deductions/expenses"""
        template = """Extract all deductions and expenses from this salary slip.

Context: {context}

Return a JSON array of deductions, each with:
- component: name (e.g., "PF", "Tax", "Insurance")
- amount: amount in currency format

Focus on:
- PF (Provident Fund)
- Tax deductions (TDS, Income Tax)
- Insurance
- Other deductions

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("deductions PF tax insurance") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _analyze_tax_flags(self, retriever, salary_data: List[Dict]) -> List[Dict[str, str]]:
        """Analyze tax-related flags"""
        template = """Analyze this salary slip for tax-related issues and flags.

Context: {context}

Return a JSON array of tax flags, each with:
- title: brief flag title
- message: detailed explanation of the tax issue

Look for:
- Incorrect tax calculations
- Missing tax exemptions
- HRA calculation issues
- Section 80C/80D deductions
- Tax bracket optimization opportunities
- Missing investment declarations

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("tax TDS HRA exemptions deductions") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _find_mistakes(self, retriever, salary_data: List[Dict], expenses_data: List[Dict]) -> List[Dict[str, str]]:
        """Find mistakes in salary slip calculations"""
        template = """Find any mistakes or discrepancies in this salary slip.

Context: {context}

Return a JSON array of mistakes, each with:
- title: brief mistake title
- message: detailed explanation of the mistake

Check for:
- Calculation errors
- Missing components
- Incorrect PF calculations
- Wrong tax deductions
- Mismatched totals
- Missing signatures/dates

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("calculations totals PF tax errors") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _suggest_savings(self, salary_data: List[Dict], expenses_data: List[Dict]) -> List[str]:
        """Suggest savings opportunities"""
        # Calculate totals
        gross_salary = sum(float(item.get("amount", "0").replace("₹", "").replace(",", "").replace("$", "").replace(",", "")) 
                          for item in salary_data if item.get("amount"))
        total_deductions = sum(float(item.get("amount", "0").replace("₹", "").replace(",", "").replace("$", "").replace(",", "")) 
                              for item in expenses_data if item.get("amount"))
        net_salary = gross_salary - total_deductions
        
        suggestions = []
        
        if net_salary > 0:
            # Suggest investment in tax-saving instruments
            if net_salary > 50000:
                suggestions.append("Consider investing in ELSS (Equity Linked Savings Scheme) for tax benefits under Section 80C")
            
            if net_salary > 30000:
                suggestions.append("Maximize HRA exemption by providing rent receipts if applicable")
            
            suggestions.append(f"Consider investing 20-30% of net salary (₹{int(net_salary * 0.25):,}) in SIP for long-term wealth creation")
            
            suggestions.append("Review and optimize tax deductions to maximize take-home salary")
        
        return suggestions
    
    def _calculate_sip_planning(self, salary_data: List[Dict], expenses_data: List[Dict]) -> Dict[str, Any]:
        """Calculate SIP planning recommendations"""
        # Calculate net salary
        gross_salary = sum(float(item.get("amount", "0").replace("₹", "").replace(",", "").replace("$", "").replace(",", "")) 
                          for item in salary_data if item.get("amount"))
        total_deductions = sum(float(item.get("amount", "0").replace("₹", "").replace(",", "").replace("$", "").replace(",", "")) 
                              for item in expenses_data if item.get("amount"))
        net_salary = gross_salary - total_deductions
        
        if net_salary <= 0:
            return {
                "recommendedMonthlySIP": 0,
                "expectedReturns": {},
                "investmentCategories": []
            }
        
        # Recommended SIP: 20-30% of net salary
        recommended_sip = int(net_salary * 0.25)  # 25% of net salary
        
        # Expected returns (assuming 12% annual return)
        annual_return = 0.12
        monthly_return = annual_return / 12
        
        def calculate_sip_future_value(monthly_investment, years, monthly_rate):
            months = years * 12
            if monthly_rate == 0:
                return monthly_investment * months
            return monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        
        returns_3y = calculate_sip_future_value(recommended_sip, 3, monthly_return)
        returns_5y = calculate_sip_future_value(recommended_sip, 5, monthly_return)
        returns_10y = calculate_sip_future_value(recommended_sip, 10, monthly_return)
        
        return {
            "recommendedMonthlySIP": recommended_sip,
            "expectedReturns": {
                "3years": {
                    "invested": recommended_sip * 36,
                    "returns": int(returns_3y - (recommended_sip * 36)),
                    "total": int(returns_3y)
                },
                "5years": {
                    "invested": recommended_sip * 60,
                    "returns": int(returns_5y - (recommended_sip * 60)),
                    "total": int(returns_5y)
                },
                "10years": {
                    "invested": recommended_sip * 120,
                    "returns": int(returns_10y - (recommended_sip * 120)),
                    "total": int(returns_10y)
                }
            },
            "investmentCategories": [
                {
                    "category": "Large Cap Funds",
                    "allocation": "40%",
                    "amount": int(recommended_sip * 0.4),
                    "description": "Stable, established companies"
                },
                {
                    "category": "Mid Cap Funds",
                    "allocation": "30%",
                    "amount": int(recommended_sip * 0.3),
                    "description": "Growth potential with moderate risk"
                },
                {
                    "category": "Small Cap Funds",
                    "allocation": "20%",
                    "amount": int(recommended_sip * 0.2),
                    "description": "High growth potential, higher risk"
                },
                {
                    "category": "Debt Funds",
                    "allocation": "10%",
                    "amount": int(recommended_sip * 0.1),
                    "description": "Stability and liquidity"
                }
            ]
        }

