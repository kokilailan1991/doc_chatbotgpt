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
        """Comprehensive salary slip analysis - optimized and accurate"""
        
        # Get all document content once
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("salary slip payroll") if hasattr(retriever, 'get_relevant_documents') else []
        if not docs:
            docs = retriever.get_relevant_documents("document") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        # Single comprehensive extraction with calculation verification
        comprehensive_template = """Extract ALL data from this salary slip accurately and verify calculations.

Salary Slip Document: {{context}}

Extract and return a JSON object with:
- employeeInfo: object with name, employeeId, designation, department, month, year, companyName, panNumber, bankAccount, ifscCode
- earnings: array of earning components (each with component name and amount as number, e.g., {{"component": "Basic Salary", "amount": 50000}})
- deductions: array of deduction components (each with component name and amount as number)
- totals: object with totalEarnings (sum of all earnings), totalDeductions (sum of all deductions), netPay (totalEarnings - totalDeductions)
- documentTotals: object with totalEarningsFromDoc (exact value stated in document), totalDeductionsFromDoc (exact value stated), netPayFromDoc (exact value stated)
- calculationErrors: array of calculation discrepancies found (e.g., "Sum of earnings components (₹80,000) does not match stated Total Earnings (₹90,000)")

IMPORTANT:
- Extract EXACT values from the document - do NOT create sample data
- Use the exact component names as they appear (e.g., "BASIC", "HRA", "CONVEYANCE ALLOWANCE", "PROF. TAX", "PF", "TDS")
- Convert amounts to numbers (remove currency symbols and commas)
- Verify all calculations match the document
- If totals don't match, include in calculationErrors

Return ONLY valid JSON, no additional text.
"""
        
        # Replace double braces with single for context variable
        formatted_template = comprehensive_template.replace("{{context}}", "{context}")
        prompt = PromptTemplate.from_template(formatted_template)
        chain = prompt | self.llm | self.output_parser
        
        try:
            result = chain.invoke({"context": content[:8000]})
            
            # Parse comprehensive result
            if result.strip().startswith('{'):
                extracted_data = json.loads(result)
            else:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = {}
            
            # Format salary and expenses data for display
            salary_data = []
            for item in extracted_data.get("earnings", []):
                component = item.get("component", "")
                amount = item.get("amount", 0)
                # Format amount with currency
                if isinstance(amount, (int, float)):
                    salary_data.append({
                        "component": component,
                        "amount": f"₹{amount:,.2f}".replace(".00", "")
                    })
                else:
                    salary_data.append({
                        "component": component,
                        "amount": str(amount)
                    })
            
            expenses_data = []
            for item in extracted_data.get("deductions", []):
                component = item.get("component", "")
                amount = item.get("amount", 0)
                # Format amount with currency
                if isinstance(amount, (int, float)):
                    expenses_data.append({
                        "component": component,
                        "amount": f"₹{amount:,.2f}".replace(".00", "")
                    })
                else:
                    expenses_data.append({
                        "component": component,
                        "amount": str(amount)
                    })
            
            # Calculate totals from extracted components
            calculated_total_earnings = sum(
                float(str(item.get("amount", 0)).replace("₹", "").replace(",", "").replace("$", "")) 
                for item in extracted_data.get("earnings", []) if isinstance(item.get("amount"), (int, float))
            )
            calculated_total_deductions = sum(
                float(str(item.get("amount", 0)).replace("₹", "").replace(",", "").replace("$", "")) 
                for item in extracted_data.get("deductions", []) if isinstance(item.get("amount"), (int, float))
            )
            calculated_net_pay = calculated_total_earnings - calculated_total_deductions
            
            # Get document totals
            doc_totals = extracted_data.get("totals", {})
            doc_earnings = doc_totals.get("totalEarningsFromDoc") or doc_totals.get("totalEarnings", calculated_total_earnings)
            doc_deductions = doc_totals.get("totalDeductionsFromDoc") or doc_totals.get("totalDeductions", calculated_total_deductions)
            doc_net_pay = doc_totals.get("netPayFromDoc") or doc_totals.get("netPay", calculated_net_pay)
            
            # Create accurate summary using extracted data
            employee_info = extracted_data.get("employeeInfo", {})
            employee_name = employee_info.get("name", "Employee")
            month = employee_info.get("month", "")
            year = employee_info.get("year", "")
            period = f"{month} {year}".strip() if month or year else "the period"
            
            # Format amounts for summary
            gross_str = f"₹{calculated_total_earnings:,.0f}"
            net_str = f"₹{calculated_net_pay:,.0f}"
            deductions_str = f"₹{calculated_total_deductions:,.0f}"
            
            # Get main deduction components for summary
            main_deductions = []
            for item in extracted_data.get("deductions", []):
                comp = item.get("component", "")
                if any(keyword in comp.upper() for keyword in ["TAX", "TDS", "PF", "PROF"]):
                    main_deductions.append(comp)
            
            summary = f"The salary slip for {period} details that employee {employee_name}"
            if employee_info.get("employeeId"):
                summary += f" (ID: {employee_info.get('employeeId')})"
            summary += f" has a gross salary of {gross_str} and a net pay of {net_str}. "
            
            if main_deductions:
                summary += f"Key deductions include {', '.join(main_deductions[:3])} totaling {deductions_str}."
            else:
                summary += f"Total deductions amount to {deductions_str}."
            
            # Analyze tax flags and mistakes
            tax_flags = self._analyze_tax_flags_optimized(retriever, extracted_data)
            mistakes = extracted_data.get("calculationErrors", [])
            
            # Add calculation verification to mistakes
            doc_earnings_num = doc_earnings if isinstance(doc_earnings, (int, float)) else None
            doc_net_pay_num = doc_net_pay if isinstance(doc_net_pay, (int, float)) else None
            
            if doc_earnings_num and abs(calculated_total_earnings - doc_earnings_num) > 1:
                mistakes.append({
                    "title": "Total Earnings Mismatch",
                    "message": f"Sum of earnings components (₹{calculated_total_earnings:,.2f}) does not match stated Total Earnings in document (₹{doc_earnings_num:,.2f}). Difference: ₹{abs(calculated_total_earnings - doc_earnings_num):,.2f}. Please verify calculations."
                })
            
            if doc_net_pay_num and abs(calculated_net_pay - doc_net_pay_num) > 1:
                expected_net = (doc_earnings_num if doc_earnings_num else calculated_total_earnings) - calculated_total_deductions
                mistakes.append({
                    "title": "Net Pay Calculation Error",
                    "message": f"Calculated Net Pay (₹{calculated_net_pay:,.2f}) does not match stated Net Pay in document (₹{doc_net_pay_num:,.2f}). Expected calculation: Total Earnings - Total Deductions = ₹{expected_net:,.2f}. Difference: ₹{abs(calculated_net_pay - doc_net_pay_num):,.2f}."
                })
            
            # Verify: Total Earnings - Total Deductions = Net Pay
            expected_net_from_calc = calculated_total_earnings - calculated_total_deductions
            if abs(calculated_net_pay - expected_net_from_calc) > 1:
                mistakes.append({
                    "title": "Calculation Verification Failed",
                    "message": f"Net Pay calculation verification: Total Earnings (₹{calculated_total_earnings:,.2f}) - Total Deductions (₹{calculated_total_deductions:,.2f}) = ₹{expected_net_from_calc:,.2f}, but Net Pay shows ₹{calculated_net_pay:,.2f}. There is a discrepancy of ₹{abs(calculated_net_pay - expected_net_from_calc):,.2f}."
                })
            
            # Calculate SIP and savings using accurate net pay
            sip_planning = self._calculate_sip_planning_from_amounts(calculated_net_pay)
            savings_suggestions = self._suggest_savings_from_amounts(calculated_net_pay, calculated_total_earnings)
            
            return {
                "summary": summary,
                "salaryData": salary_data,
                "expensesData": expenses_data,
                "taxFlags": tax_flags,
                "mistakes": mistakes,
                "savingsSuggestions": savings_suggestions,
                "sipPlanning": sip_planning,
                "netPay": f"₹{calculated_net_pay:,.2f}".replace(".00", ""),
                "totalEarnings": f"₹{calculated_total_earnings:,.2f}".replace(".00", ""),
                "totalDeductions": f"₹{calculated_total_deductions:,.2f}".replace(".00", "")
            }
        except Exception as e:
            print(f"Error in comprehensive salary slip analysis: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic analysis
            return {
                "summary": "Error analyzing salary slip. Please try again.",
                "salaryData": [],
                "expensesData": [],
                "taxFlags": [],
                "mistakes": [{"title": "Analysis Error", "message": str(e)}],
                "savingsSuggestions": [],
                "sipPlanning": {}
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
    
    def _analyze_tax_flags_optimized(self, retriever, extracted_data: Dict) -> List[Dict[str, str]]:
        """Analyze tax-related flags using extracted data"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("tax TDS HRA exemptions deductions") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        # Get earnings and deductions for context
        earnings_summary = ", ".join([f"{item.get('component', '')}: ₹{item.get('amount', 0):,.0f}" 
                                      for item in extracted_data.get("earnings", [])[:5]])
        deductions_summary = ", ".join([f"{item.get('component', '')}: ₹{item.get('amount', 0):,.0f}" 
                                        for item in extracted_data.get("deductions", [])])
        
        template = """Analyze this salary slip for tax-related issues and flags.

Document Context: {{context}}

Extracted Data:
- Earnings: {earnings_summary}
- Deductions: {deductions_summary}
- Net Pay: ₹{net_pay:,.0f}

Return a JSON array of tax flags, each with:
- title: brief flag title
- message: detailed explanation of the tax issue

Look for:
- Incorrect tax calculations (verify TDS matches income tax slabs)
- Missing tax exemptions (HRA, transport allowance, medical)
- HRA calculation issues (should not exceed 50% of basic in metro cities)
- Section 80C/80D deductions opportunities
- Tax bracket optimization opportunities
- Missing investment declarations

Return ONLY valid JSON array, no additional text.
"""
        
        totals = extracted_data.get("totals", {})
        net_pay = totals.get("netPay") or (totals.get("totalEarnings", 0) - totals.get("totalDeductions", 0))
        
        formatted_template = template.replace("{{context}}", "{context}").format(
            earnings_summary=earnings_summary,
            deductions_summary=deductions_summary,
            net_pay=net_pay if isinstance(net_pay, (int, float)) else 0
        )
        
        prompt = PromptTemplate.from_template(formatted_template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:6000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing tax flags: {e}")
        
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
    
    def _suggest_savings_from_amounts(self, net_salary: float, gross_salary: float) -> List[str]:
        """Suggest savings opportunities based on amounts"""
        suggestions = []
        
        if net_salary > 0:
            # Suggest investment in tax-saving instruments
            if net_salary > 50000:
                suggestions.append("Consider investing in ELSS (Equity Linked Savings Scheme) for tax benefits under Section 80C")
            
            if net_salary > 30000:
                suggestions.append("Maximize HRA exemption by providing rent receipts if applicable")
            
            sip_amount = int(net_salary * 0.25)
            suggestions.append(f"Consider investing 20-30% of net salary (₹{sip_amount:,}) in SIP for long-term wealth creation")
            
            suggestions.append("Review and optimize tax deductions to maximize take-home salary")
        
        return suggestions
    
    def _calculate_sip_planning_from_amounts(self, net_salary: float) -> Dict[str, Any]:
        """Calculate SIP planning recommendations from net salary amount"""
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

