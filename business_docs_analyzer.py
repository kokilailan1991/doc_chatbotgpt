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

# No external dependencies - self-contained extraction


class BusinessDocsAnalyzer:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
        self.workflow = WorkflowProcessor(openai_key)
    
    def _extract_invoice_content(self, retriever):
        """Extract invoice content with multiple fallback strategies - self-contained"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        content = ""
        docs = []
        
        # Strategy 1: Search for invoice-specific terms
        if hasattr(retriever, 'get_relevant_documents'):
            search_queries = [
                "invoice bill invoice number vendor buyer amount total payment",
                "invoice",
                "bill",
                "vendor buyer amount"
            ]
            for query in search_queries:
                try:
                    temp_docs = retriever.get_relevant_documents(query)
                    if temp_docs:
                        temp_content = format_docs(temp_docs)
                        if len(temp_content.strip()) > len(content.strip()):
                            content = temp_content
                            docs = temp_docs
                except:
                    continue
        
        # Strategy 2: Broader search
        if len(content.strip()) < 200:
            broad_queries = ["document", "text", "content", ""]
            for query in broad_queries:
                try:
                    if hasattr(retriever, 'get_relevant_documents'):
                        temp_docs = retriever.get_relevant_documents(query)
                        if temp_docs:
                            temp_content = format_docs(temp_docs)
                            if len(temp_content.strip()) > len(content.strip()):
                                content = temp_content
                                docs = temp_docs
                except:
                    continue
        
        # Strategy 3: Direct vectorstore access
        if len(content.strip()) < 200:
            try:
                vectorstore = None
                if hasattr(retriever, 'vectorstore'):
                    vectorstore = retriever.vectorstore
                elif hasattr(retriever, '_vectorstore'):
                    vectorstore = retriever._vectorstore
                
                if vectorstore:
                    try:
                        all_docs = vectorstore.similarity_search("", k=200)
                        if all_docs:
                            temp_content = format_docs(all_docs)
                            if len(temp_content.strip()) > len(content.strip()):
                                content = temp_content
                                docs = all_docs
                    except:
                        pass
            except:
                pass
        
        return content, docs
    
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
        """Comprehensive detailed invoice analysis with accurate extraction and calculation verification"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Self-contained extraction
        content, docs = self._extract_invoice_content(retriever)
        
        # Final check - be more lenient with minimum content
        if not content or len(content.strip()) < 20:
            error_msg = "Could not extract sufficient content from the invoice PDF. "
            error_msg += "Possible reasons: "
            error_msg += "1) The PDF might be image-based/scanned (requires OCR), "
            error_msg += "2) The PDF might be corrupted, "
            error_msg += "3) The PDF might not contain selectable text. "
            error_msg += "Please ensure the PDF contains selectable text or try converting it to a text-based PDF."
            print(f"ERROR: Invoice extraction failed. Content length: {len(content) if content else 0} characters")
            print(f"Number of docs retrieved: {len(docs) if docs else 0}")
            return {
                "documentType": "Invoice",
                "error": error_msg,
                "summary": "",
                "financialDetails": {},
                "lineItemsAnalysis": {},
                "paymentAnalysis": {},
                "riskAnalysis": {},
                "tables": []
            }
        
        # Log content length for debugging
        print(f"Invoice content extracted: {len(content)} characters from {len(docs) if docs else 0} document chunks")
        
        # Single comprehensive extraction to ensure consistency
        comprehensive_template = """Extract ALL data from this invoice accurately. Extract EXACT values from the document - do NOT create sample or example data.

Invoice Document: {{context}}

Extract and return a JSON object with:
- invoiceNumber: exact invoice number from document
- invoiceDate: exact date from document
- dueDate: exact due date from document
- vendorName: exact vendor/seller name from document
- vendorAddress: exact vendor address from document
- vendorGST: GST number if present
- vendorPAN: PAN number if present
- buyerName: exact buyer/recipient name from document
- buyerAddress: exact buyer address from document
- buyerGST: GST number if present
- buyerPAN: PAN number if present
- subtotal: subtotal amount as number (remove currency symbols)
- taxBreakdown: array of tax objects, each with taxType (e.g., "CGST", "SGST", "IGST", "GST"), taxRate (as number), taxAmount (as number), taxableAmount (as number)
- discount: discount amount as number (0 if not present)
- shippingCharges: shipping amount as number (0 if not present)
- totalAmount: total amount as number from document
- currency: currency code (e.g., "USD", "INR", "₹", "$")
- paymentTerms: exact payment terms from document
- paymentMethod: payment method if mentioned
- paymentTransactionID: transaction ID if present
- lineItems: array of line item objects, each with itemNumber, description, quantity (as number), unitPrice (as number), totalPrice (as number), taxRate (as number), taxAmount (as number), category
- lineItemsCount: total number of line items
- lineItemsTotal: sum of all line item totalPrice values

IMPORTANT:
- Extract ONLY actual values from the document
- Use exact names, dates, and amounts as they appear
- Convert amounts to numbers (remove currency symbols and commas)
- Verify calculations: subtotal + sum of all taxes - discount + shipping = totalAmount
- If calculations don't match, note it in calculationErrors

Return ONLY valid JSON, no additional text.
"""
        
        # Replace double braces with single for context variable
        formatted_template = comprehensive_template.replace("{{context}}", "{context}")
        
        try:
            prompt = PromptTemplate.from_template(formatted_template)
        except Exception as e:
            print(f"ERROR: Failed to create prompt template: {e}")
            return {
                "documentType": "Invoice",
                "error": f"Template processing error: {str(e)}",
                "summary": "",
                "financialDetails": {},
                "lineItemsAnalysis": {},
                "paymentAnalysis": {},
                "riskAnalysis": {},
                "tables": []
            }
        
        chain = prompt | self.llm | self.output_parser
        
        try:
            # Ensure content is a string and not empty
            content_str = str(content) if content else ""
            if not content_str.strip():
                raise ValueError("Content is empty")
            
            comprehensive_data = chain.invoke({"context": content_str[:10000]})
            
            # Parse comprehensive result
            if comprehensive_data.strip().startswith('{'):
                extracted_data = json.loads(comprehensive_data)
            else:
                json_match = re.search(r'\{.*\}', comprehensive_data, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = {}
            
            # Verify calculations
            calculation_errors = []
            subtotal = extracted_data.get("subtotal", 0) or 0
            discount = extracted_data.get("discount", 0) or 0
            shipping = extracted_data.get("shippingCharges", 0) or 0
            total_tax = sum(tax.get("taxAmount", 0) or 0 for tax in extracted_data.get("taxBreakdown", []))
            stated_total = extracted_data.get("totalAmount", 0) or 0
            
            calculated_total = subtotal + total_tax - discount + shipping
            
            if abs(calculated_total - stated_total) > 0.01:  # Allow small rounding differences
                calculation_errors.append({
                    "title": "Total Amount Calculation Mismatch",
                    "message": f"Calculated total (Subtotal: {subtotal} + Tax: {total_tax} - Discount: {discount} + Shipping: {shipping} = {calculated_total}) does not match stated total ({stated_total}). Difference: {abs(calculated_total - stated_total)}"
                })
            
            # Verify line items total
            line_items = extracted_data.get("lineItems", [])
            line_items_total = sum(float(item.get("totalPrice", 0) or 0) for item in line_items)
            if line_items and abs(line_items_total - subtotal) > 0.01:
                calculation_errors.append({
                    "title": "Line Items Total Mismatch",
                    "message": f"Sum of line items ({line_items_total}) does not match subtotal ({subtotal}). Difference: {abs(line_items_total - subtotal)}"
                })
            
            # Separate financial info and line items
            financial_info = {
                "invoiceNumber": extracted_data.get("invoiceNumber"),
                "invoiceDate": extracted_data.get("invoiceDate"),
                "dueDate": extracted_data.get("dueDate"),
                "vendorName": extracted_data.get("vendorName"),
                "vendorAddress": extracted_data.get("vendorAddress"),
                "vendorGST": extracted_data.get("vendorGST"),
                "vendorPAN": extracted_data.get("vendorPAN"),
                "buyerName": extracted_data.get("buyerName"),
                "buyerAddress": extracted_data.get("buyerAddress"),
                "buyerGST": extracted_data.get("buyerGST"),
                "buyerPAN": extracted_data.get("buyerPAN"),
                "subtotal": subtotal,
                "taxBreakdown": extracted_data.get("taxBreakdown", []),
                "discount": discount,
                "shippingCharges": shipping,
                "totalAmount": stated_total,
                "currency": extracted_data.get("currency", "USD"),
                "paymentTerms": extracted_data.get("paymentTerms"),
                "paymentMethod": extracted_data.get("paymentMethod"),
                "paymentTransactionID": extracted_data.get("paymentTransactionID"),
                "lineItemsCount": extracted_data.get("lineItemsCount", len(line_items)),
                "lineItemsTotal": line_items_total
            }
            
            # Prepare line items analysis
            line_items_info = {
                "lineItems": line_items,
                "lineItemsSummary": {
                    "totalItems": len(line_items),
                    "categories": {},
                    "averageItemValue": line_items_total / len(line_items) if line_items else 0,
                    "highestValueItem": None,
                    "lowestValueItem": None
                }
            }
            
            # Calculate categories and find highest/lowest
            if line_items:
                for item in line_items:
                    category = item.get("category", "Uncategorized")
                    line_items_info["lineItemsSummary"]["categories"][category] = line_items_info["lineItemsSummary"]["categories"].get(category, 0) + 1
                
                # Find highest and lowest value items
                highest = max(line_items, key=lambda x: float(x.get("totalPrice", 0) or 0))
                lowest = min(line_items, key=lambda x: float(x.get("totalPrice", 0) or 0))
                
                line_items_info["lineItemsSummary"]["highestValueItem"] = {
                    "description": highest.get("description", ""),
                    "totalPrice": highest.get("totalPrice", 0)
                }
                line_items_info["lineItemsSummary"]["lowestValueItem"] = {
                    "description": lowest.get("description", ""),
                    "totalPrice": lowest.get("totalPrice", 0)
                }
            
        except Exception as e:
            print(f"Error in comprehensive invoice extraction: {e}")
            import traceback
            traceback.print_exc()
            financial_info = {}
            line_items_info = {"lineItems": [], "lineItemsSummary": {}}
            calculation_errors = [{"title": "Extraction Error", "message": str(e)}]
        
        # 2. Risk and compliance analysis using extracted data
        risk_template = """Perform a comprehensive risk and compliance analysis of this invoice using the extracted data.

Invoice Document: {{context}}

Extracted Financial Data:
- Vendor: {vendor_name}
- Buyer: {buyer_name}
- Total Amount: {currency} {total_amount}
- Subtotal: {currency} {subtotal}
- Taxes: {currency} {total_tax}
- Discount: {currency} {discount}
- Shipping: {currency} {shipping}
- Line Items Count: {line_items_count}

Return a JSON object with: risks (array of risk objects with title, description, severity, category, evidence, impact, recommendation, affectedAmount), complianceIssues (array), missingInformation (array), duplicateCharges (array), suspiciousPatterns (array).

Each risk object should have: title, description (3-5 sentences), severity (high/medium/low), category, evidence, impact, recommendation, affectedAmount.

Return ONLY valid JSON, no additional text.
"""
            
        formatted_risk_template = risk_template.replace("{{context}}", "{context}").format(
            vendor_name=financial_info.get("vendorName", "Unknown"),
            buyer_name=financial_info.get("buyerName", "Unknown"),
            currency=financial_info.get("currency", ""),
            total_amount=financial_info.get("totalAmount", 0),
            subtotal=financial_info.get("subtotal", 0),
            total_tax=sum(tax.get("taxAmount", 0) or 0 for tax in financial_info.get("taxBreakdown", [])),
            discount=financial_info.get("discount", 0),
            shipping=financial_info.get("shippingCharges", 0),
            line_items_count=line_items_info.get("lineItemsSummary", {}).get("totalItems", 0)
        )
        
        try:
            prompt = PromptTemplate.from_template(formatted_risk_template)
            chain = prompt | self.llm | self.output_parser
            content_str = str(content) if content else ""
            risk_data = chain.invoke({"context": content_str[:8000]})
        except Exception as e:
            print(f"ERROR in risk analysis: {e}")
            risk_data = "{}"
        
        risk_info = {"risks": [], "complianceIssues": [], "missingInformation": [], "duplicateCharges": [], "suspiciousPatterns": []}
        try:
            if risk_data.strip().startswith('{'):
                risk_info = json.loads(risk_data)
            else:
                json_match = re.search(r'\{.*\}', risk_data, re.DOTALL)
                if json_match:
                    risk_info = json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing risk data: {e}")
        
        # Add calculation errors to risk info
        risk_info["calculationErrors"] = calculation_errors
    
        # 3. Payment and terms analysis using extracted data
        payment_template = """Analyze payment terms and payment-related information from this invoice.

Invoice Document: {{context}}

Extracted Data:
- Payment Terms: {payment_terms}
- Due Date: {due_date}
- Payment Method: {payment_method}
- Transaction ID: {transaction_id}

Return a JSON object with: paymentTerms (object with terms, dueDate, daysUntilDue, earlyPaymentDiscount, latePaymentPenalty, paymentMethods), paymentStatus, bankDetails (object with accountNumber, bankName, ifscCode, swiftCode if found in document), recommendations (array).

Return ONLY valid JSON, no additional text.
"""
            
        formatted_payment_template = payment_template.replace("{{context}}", "{context}").format(
            payment_terms=financial_info.get("paymentTerms", ""),
            due_date=financial_info.get("dueDate", ""),
            payment_method=financial_info.get("paymentMethod", ""),
            transaction_id=financial_info.get("paymentTransactionID", "")
        )
        
        prompt = PromptTemplate.from_template(formatted_payment_template)
        chain = prompt | self.llm | self.output_parser
        payment_data = chain.invoke({"context": content[:8000]})
        
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
        
        # 4. Create accurate summary using extracted data
        vendor_name = financial_info.get("vendorName", "Unknown Vendor")
        buyer_name = financial_info.get("buyerName", "Unknown Buyer")
        invoice_num = financial_info.get("invoiceNumber", "N/A")
        invoice_date = financial_info.get("invoiceDate", "N/A")
        due_date = financial_info.get("dueDate", "N/A")
        currency = financial_info.get("currency", "")
        total = financial_info.get("totalAmount", 0)
        subtotal = financial_info.get("subtotal", 0)
        total_tax = sum(tax.get("taxAmount", 0) or 0 for tax in financial_info.get("taxBreakdown", []))
        discount = financial_info.get("discount", 0)
        shipping = financial_info.get("shippingCharges", 0)
        line_items_count = line_items_info.get("lineItemsSummary", {}).get("totalItems", 0)
        payment_terms = financial_info.get("paymentTerms", "Not specified")
        
        detailed_summary = f"This invoice is from {vendor_name} to {buyer_name}, with invoice number {invoice_num}, dated {invoice_date}, and due on {due_date}. "
        detailed_summary += f"The total amount is {currency} {total}. "
        detailed_summary += f"The breakdown includes a subtotal of {currency} {subtotal}, "
        if total_tax > 0:
            detailed_summary += f"taxes totaling {currency} {total_tax}, "
        if discount > 0:
            detailed_summary += f"a discount of {currency} {discount}, "
        if shipping > 0:
            detailed_summary += f"and shipping charges of {currency} {shipping}. "
        detailed_summary += f"The invoice contains {line_items_count} line item(s). "
        detailed_summary += f"Payment terms are: {payment_terms}. "
        
        if financial_info.get("vendorGST") or financial_info.get("vendorPAN"):
            detailed_summary += f"Vendor GST: {financial_info.get('vendorGST', 'N/A')}, PAN: {financial_info.get('vendorPAN', 'N/A')}. "
        if financial_info.get("buyerGST") or financial_info.get("buyerPAN"):
            detailed_summary += f"Buyer GST: {financial_info.get('buyerGST', 'N/A')}, PAN: {financial_info.get('buyerPAN', 'N/A')}. "
        
        if calculation_errors:
            detailed_summary += f"Note: {len(calculation_errors)} calculation discrepancy(ies) detected. Please verify the invoice totals carefully."
        
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







