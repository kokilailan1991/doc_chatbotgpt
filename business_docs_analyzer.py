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
        template = """Extract all tables, line items, and structured data from this document. Extract ONLY the actual data present in the document - do NOT create sample or example data.
        
Document: {context}

Return a JSON array of tables, each with:
- tableName: name/description of the table (e.g., "Line Items", "Invoice Items", "Products")
- headers: [array of column headers found in the document]
- rows: [array of row objects with actual column values from the document]
- totalAmount: total amount if found in the document
- currency: currency code if found in the document

IMPORTANT: 
- Extract ONLY data that actually exists in the document
- Do NOT create sample data like "Product A", "Product B"
- Do NOT create example dates like "2022-01-01"
- If no data is found, return an empty array
- Use the exact values, dates, and items from the document

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("invoice line items products services") if hasattr(retriever, 'get_relevant_documents') else []
        if not docs:
            # Try broader search
            docs = retriever.get_relevant_documents("document") if hasattr(retriever, 'get_relevant_documents') else []
        
        content = format_docs(docs) if docs else ""
        
        if not content or len(content.strip()) < 50:
            # Not enough content to extract
            return []
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:8000]})  # Increased context window
        
        try:
            if result.strip().startswith('['):
                parsed = json.loads(result)
                # Validate that it's not sample data
                if parsed and len(parsed) > 0:
                    first_table = parsed[0]
                    if first_table.get('rows'):
                        first_row = first_table['rows'][0]
                        # Check for common sample data patterns
                        sample_patterns = ['Product A', 'Product B', 'Product C', 'Sample', 'Example', 'Test']
                        row_str = json.dumps(first_row).lower()
                        if any(pattern.lower() in row_str for pattern in sample_patterns):
                            # Likely sample data, return empty
                            return []
                return parsed
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # Same validation
                if parsed and len(parsed) > 0:
                    first_table = parsed[0]
                    if first_table.get('rows'):
                        first_row = first_table['rows'][0]
                        row_str = json.dumps(first_row).lower()
                        sample_patterns = ['Product A', 'Product B', 'Product C', 'Sample', 'Example', 'Test']
                        if any(pattern.lower() in row_str for pattern in sample_patterns):
                            return []
                return parsed
        except Exception as e:
            print(f"Error parsing tables: {e}")
            pass
        
        return []
    
    def analyze_invoice_detailed(self, retriever) -> Dict[str, Any]:
        """Comprehensive detailed invoice analysis with financial breakdowns"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Get full document content
        docs = retriever.get_relevant_documents("invoice") if hasattr(retriever, 'get_relevant_documents') else []
        if not docs:
            docs = retriever.get_relevant_documents("document") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        # 1. Extract detailed financial information
        financial_template = """Analyze this invoice and extract ALL financial details in JSON format.

Invoice Document: {context}

Extract and return a JSON object with:
- invoiceNumber: invoice number or ID
- invoiceDate: invoice date
- dueDate: payment due date
- vendorName: name of the vendor/supplier
- vendorAddress: vendor's address
- vendorGST: vendor GST registration number (if applicable)
- vendorPAN: vendor PAN number (if applicable)
- buyerName: buyer/customer name
- buyerAddress: buyer's address
- buyerGST: buyer GST registration number (if applicable)
- buyerPAN: buyer PAN number (if applicable)
- subtotal: subtotal amount before taxes
- taxBreakdown: [array of tax objects with: taxType (e.g., "GST", "VAT", "Sales Tax"), taxRate (percentage), taxAmount, taxableAmount]
- discount: discount amount (if any)
- shippingCharges: shipping/delivery charges (if any)
- totalAmount: final total amount
- currency: currency code (INR, USD, etc.)
- paymentTerms: payment terms (e.g., "Net 30", "Due on receipt")
- paymentMethod: payment method mentioned
- paymentTransactionID: payment transaction ID (if any)
- lineItemsCount: number of line items
- lineItemsTotal: sum of all line item amounts

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(financial_template)
        chain = prompt | self.llm | self.output_parser
        financial_data = chain.invoke({"context": content[:10000]})
        
        financial_info = {}
        try:
            if financial_data.strip().startswith('{'):
                financial_info = json.loads(financial_data)
            else:
                json_match = re.search(r'\{.*\}', financial_data, re.DOTALL)
                if json_match:
                    financial_info = json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing financial data: {e}")
        
        # 2. Detailed risk and compliance analysis
        risk_template = """Perform a comprehensive risk and compliance analysis of this invoice.

Invoice Document: {context}

Return a JSON object with:
- risks: [array of risk objects, each with:
    - title: risk title
    - description: detailed explanation of the risk (3-5 sentences explaining why it's a risk, what could go wrong, and potential impact)
    - severity: "high", "medium", or "low"
    - category: risk category (e.g., "Tax Compliance", "Data Security", "Payment Issues", "Documentation", "Financial")
    - evidence: specific evidence from the invoice that supports this risk (quote exact values, dates, or text)
    - impact: potential impact if this risk materializes
    - recommendation: specific recommendation to mitigate this risk
    - affectedAmount: amount affected by this risk (if applicable)
]
- complianceIssues: [array of compliance issues with detailed explanations]
- calculationErrors: [array of calculation errors found (e.g., "Subtotal + Tax should equal Total but shows discrepancy of X")]
- missingInformation: [array of missing critical information]
- duplicateCharges: [array of any duplicate charges found]
- suspiciousPatterns: [array of suspicious patterns detected with detailed explanations]

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(risk_template)
        chain = prompt | self.llm | self.output_parser
        risk_data = chain.invoke({"context": content[:10000]})
        
        risk_info = {"risks": [], "complianceIssues": [], "calculationErrors": [], "missingInformation": [], "duplicateCharges": [], "suspiciousPatterns": []}
        try:
            if risk_data.strip().startswith('{'):
                risk_info = json.loads(risk_data)
            else:
                json_match = re.search(r'\{.*\}', risk_data, re.DOTALL)
                if json_match:
                    risk_info = json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing risk data: {e}")
        
        # 3. Detailed line item analysis
        line_items_template = """Analyze all line items in this invoice in detail.

Invoice Document: {context}

Return a JSON object with:
- lineItems: [array of line item objects, each with:
    - itemNumber: line item number
    - description: item/service description
    - quantity: quantity
    - unitPrice: unit price
    - totalPrice: total price for this line
    - taxRate: tax rate applied (if any)
    - taxAmount: tax amount for this line (if any)
    - category: item category (e.g., "Product", "Service", "Shipping")
    - notes: any notes or special conditions for this item
]
- lineItemsSummary: {
    - totalItems: total number of line items
    - categories: [array of categories with item counts]
    - highestValueItem: item with highest value
    - lowestValueItem: item with lowest value
    - averageItemValue: average value per item
}

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(line_items_template)
        chain = prompt | self.llm | self.output_parser
        line_items_data = chain.invoke({"context": content[:10000]})
        
        line_items_info = {"lineItems": [], "lineItemsSummary": {}}
        try:
            if line_items_data.strip().startswith('{'):
                line_items_info = json.loads(line_items_data)
            else:
                json_match = re.search(r'\{.*\}', line_items_data, re.DOTALL)
                if json_match:
                    line_items_info = json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing line items data: {e}")
        
        # 4. Payment and terms analysis
        payment_template = """Analyze payment terms, conditions, and payment-related information in this invoice.

Invoice Document: {context}

Return a JSON object with:
- paymentTerms: {
    - terms: payment terms text
    - dueDate: due date
    - daysUntilDue: number of days until due date
    - earlyPaymentDiscount: early payment discount (if any)
    - latePaymentPenalty: late payment penalty (if any)
    - paymentMethods: [array of accepted payment methods]
}
- paymentStatus: current payment status (if mentioned)
- paymentHistory: any payment history mentioned
- bankDetails: {
    - accountNumber: bank account number (if mentioned)
    - bankName: bank name
    - ifscCode: IFSC code (if applicable)
    - swiftCode: SWIFT code (if applicable)
}
- recommendations: [array of payment-related recommendations]

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(payment_template)
        chain = prompt | self.llm | self.output_parser
        payment_data = chain.invoke({"context": content[:10000]})
        
        payment_info = {}
        try:
            if payment_data.strip().startswith('{'):
                payment_info = json.loads(payment_data)
            else:
                json_match = re.search(r'\{.*\}', payment_data, re.DOTALL)
                if json_match:
                    payment_info = json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing payment data: {e}")
        
        # 5. Enhanced summary with all key details
        summary_template = """Create a comprehensive, detailed summary of this invoice that includes all important information.

Invoice Document: {context}

Create a detailed summary (3-5 paragraphs) that includes:
- Overview of the invoice (vendor, buyer, invoice number, dates)
- Total amount and currency
- Breakdown of charges (subtotal, taxes, discounts, shipping)
- Number of line items and key items/services
- Payment terms and due date
- Any notable issues, risks, or concerns
- Key compliance information (GST, PAN numbers if applicable)
- Recommendations for the buyer

Return the summary as plain text (not JSON).
"""
        
        prompt = PromptTemplate.from_template(summary_template)
        chain = prompt | self.llm | self.output_parser
        detailed_summary = chain.invoke({"context": content[:10000]})
        
        # Extract tables
        tables = self.extract_tables(retriever)
        
        # Combine all information
        return {
            "documentType": "Invoice",
            "summary": detailed_summary,
            "financialDetails": financial_info,
            "lineItemsAnalysis": line_items_info,
            "paymentAnalysis": payment_info,
            "riskAnalysis": risk_info,
            "tables": tables,
            "risks": risk_info.get("risks", []),
            "complianceIssues": risk_info.get("complianceIssues", []),
            "calculationErrors": risk_info.get("calculationErrors", []),
            "missingInformation": risk_info.get("missingInformation", []),
            "duplicateCharges": risk_info.get("duplicateCharges", []),
            "suspiciousPatterns": risk_info.get("suspiciousPatterns", [])
        }
    
    def analyze_business_doc(self, retriever) -> Dict[str, Any]:
        """Comprehensive business document analysis"""
        doc_type = self.detect_document_type(retriever)
        
        # Use detailed invoice analysis for invoices
        if doc_type == "Invoice":
            return self.analyze_invoice_detailed(retriever)
        
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







